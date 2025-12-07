# MT4 AI Agent (LightGBM + ZeroMQ)

This folder contains a minimal, runnable blueprint to build an AI-driven trading agent for MetaTrader 4 (MT4).

What you get
- `train.py` — trains a LightGBM direction classifier from historical candles and saves a model + scaler.
- `server.py` — a ZeroMQ REP server that loads the trained model and returns BUY/SELL/HOLD signals.
- `mt4_ea/AIBridge_EA.mq4` — MQL4 EA template showing how to pack recent candles into JSON and send to the Python server.
- `requirements.txt` — Python dependencies.

Important notes
- This is an educational blueprint. Trading risks are real. Test thoroughly on demo accounts.
- No strategy is guaranteed to be profitable. Use strict risk management.
- You must install a ZeroMQ MQL4 wrapper (mql4-zmq or equivalent) so MT4 can use ZeroMQ. The EA currently contains placeholders; adapt to the wrapper API you install.

Quick start (Windows)

1) Create a Python virtual environment and install requirements

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2) Prepare historical data

- Export candles from MT4 into CSV with columns: `datetime,open,high,low,close,volume`.

3) Train a model

```powershell
python train.py --data path\to\candles.csv --out artifacts/model.joblib --scaler artifacts/scaler.joblib
```

4) Run the Python server (keep it running while EA is attached)

```powershell
python server.py --model artifacts/model.joblib --scaler artifacts/scaler.joblib --host 127.0.0.1 --port 5555
```

5) Configure MT4

- Install the ZeroMQ wrapper (mql4-zmq) and copy `.mqh` and `.dll` to `MQL4/Include` and `MQL4/Libraries` as required.
- Copy `AIBridge_EA.mq4` into `MQL4/Experts/` and compile in MetaEditor, adapting the ZMQ calls to your wrapper.
- Attach the EA to a chart and monitor logs.

Next steps and improvements
- Replace the EA's placeholder ZMQ calls with the wrapper's actual API (see mql4-zmq docs).
- Add model versioning and a heartbeat/health endpoint.
- Implement walk-forward testing and live monitoring/backtesting framework.
- Add slippage/spread checks, better lot-sizing (based on true pip-value), and broker-provided spread filters.

Disclaimer
This repository is a technical template. It is not financial advice. Use at your own risk.
