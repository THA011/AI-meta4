"""
train.py

Minimal training script for a LightGBM direction classifier.

Usage:
  python train.py --data path/to/candles.csv --out artifacts/model.joblib

The CSV must contain columns: datetime, open, high, low, close, volume

This script creates a model and scaler saved with joblib.
"""
import argparse
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import joblib
import os


def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / (ma_down + 1e-12)
    return 100 - (100 / (1 + rs))


def feature_engineer(df):
    df = df.copy()
    df['ret1'] = df['close'].pct_change()
    df['sma5'] = df['close'].rolling(5).mean()
    df['sma10'] = df['close'].rolling(10).mean()
    df['ema8'] = df['close'].ewm(span=8, adjust=False).mean()
    df['vol5'] = df['ret1'].rolling(5).std()
    df['rsi14'] = rsi(df['close'], period=14)
    df = df.dropna().reset_index(drop=True)
    return df


def make_label(df):
    # Next-bar direction: 1 if next close > current close else 0
    df = df.copy()
    df['next_close'] = df['close'].shift(-1)
    df = df.dropna()
    df['y'] = (df['next_close'] > df['close']).astype(int)
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', required=True)
    p.add_argument('--out', default='artifacts/model.joblib')
    p.add_argument('--scaler', default='artifacts/scaler.joblib')
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    df = pd.read_csv(args.data, parse_dates=['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    df = feature_engineer(df)
    df = make_label(df)

    features = ['sma5', 'sma10', 'ema8', 'vol5', 'rsi14', 'ret1']
    X = df[features].values
    y = df['y'].values

    # time-series split (no shuffle)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    clf = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=31)
    # Some LightGBM builds expose early_stopping_rounds in the sklearn API; others do not.
    # Try with early stopping and fall back to a plain fit for compatibility.
    try:
        clf.fit(X_train_s, y_train, eval_set=[(X_test_s, y_test)], early_stopping_rounds=30, verbose=False)
    except TypeError:
        clf.fit(X_train_s, y_train)

    joblib.dump(clf, args.out)
    joblib.dump(scaler, args.scaler)

    acc = clf.score(X_test_s, y_test)
    print(f"Saved model to {args.out}")
    print(f"Test accuracy: {acc:.4f}")


if __name__ == '__main__':
    main()
