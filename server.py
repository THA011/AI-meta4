"""
server.py

ZeroMQ REP server that accepts a JSON request with recent candles, applies identical
feature engineering and preprocessing to training, runs the saved LightGBM model, and
replies with an action (BUY/SELL/HOLD), confidence, and suggested stop/take-profit (pips).

Message format (request): JSON string or dict with keys:
 - type: "predict" | "ping"
 - candles: list of {"datetime","open","high","low","close","volume"} (for "predict")

Response (JSON): {"action":"BUY"|"SELL"|"HOLD","confidence":0.73,"stop_pips":30,"tp_pips":60}

Run:
  python server.py --model artifacts/model.joblib --scaler artifacts/scaler.joblib --port 5555
"""
import argparse
import json
import logging
import time
from typing import List

import zmq
import joblib
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)


def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / (ma_down + 1e-12)
    return 100 - (100 / (1 + rs))


def feature_engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['ret1'] = df['close'].pct_change()
    df['sma5'] = df['close'].rolling(5).mean()
    df['sma10'] = df['close'].rolling(10).mean()
    df['ema8'] = df['close'].ewm(span=8, adjust=False).mean()
    df['vol5'] = df['ret1'].rolling(5).std()
    df['rsi14'] = rsi(df['close'], period=14)
    df = df.dropna().reset_index(drop=True)
    return df


def decide_action(prob, threshold=0.55):
    if prob >= threshold:
        return 'BUY'
    elif prob <= 1 - threshold:
        return 'SELL'
    else:
        return 'HOLD'


def parse_candles(candles: List[dict]) -> pd.DataFrame:
    df = pd.DataFrame(candles)
    for c in ['open', 'high', 'low', 'close', 'volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.sort_values('datetime').reset_index(drop=True)
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--scaler', required=True)
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', default='5555')
    args = p.parse_args()

    model = joblib.load(args.model)
    scaler = joblib.load(args.scaler)

    ctx = zmq.Context()
    socket = ctx.socket(zmq.REP)
    endpoint = f"tcp://{args.host}:{args.port}"
    socket.bind(endpoint)
    logging.info(f"Server listening at {endpoint}")

    while True:
        try:
            msg = socket.recv_string()
            data = json.loads(msg)
            if data.get('type') == 'ping':
                socket.send_string(json.dumps({'status': 'ok', 'ts': int(time.time())}))
                continue

            if data.get('type') != 'predict' or 'candles' not in data:
                socket.send_string(json.dumps({'error': 'invalid request'}))
                continue

            df = parse_candles(data['candles'])
            df_fe = feature_engineer(df)
            if df_fe.empty:
                socket.send_string(json.dumps({'error': 'not enough data to compute features'}))
                continue

            # Use last row for prediction
            features = ['sma5', 'sma10', 'ema8', 'vol5', 'rsi14', 'ret1']
            x = df_fe[features].iloc[-1].values.reshape(1, -1)
            x_s = scaler.transform(x)
            prob_up = float(model.predict_proba(x_s)[0][1])
            action = decide_action(prob_up, threshold=0.56)

            # simple stop/tp suggestion: use recent ATR-like range
            recent_range = (df['high'].rolling(14).max().iloc[-1] - df['low'].rolling(14).min().iloc[-1]) / 14
            # convert to pips assuming price given in decimals (user must convert to pips as needed)
            stop_pips = max(10, int(recent_range * 10000))
            tp_pips = max(stop_pips * 2, stop_pips + 20)

            resp = {
                'action': action,
                'confidence': prob_up,
                'stop_pips': int(stop_pips),
                'tp_pips': int(tp_pips),
            }
            socket.send_string(json.dumps(resp))

        except Exception as e:
            logging.exception('Error handling request')
            try:
                socket.send_string(json.dumps({'error': str(e)}))
            except Exception:
                pass


if __name__ == '__main__':
    main()
