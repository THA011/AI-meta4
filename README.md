# MT4 Automated Trading Blueprint (LightGBM + ZeroMQ)

This repository contains a concise, production-oriented blueprint for an automated trading system that integrates a Python-based model with MetaTrader 4 (MT4) via a lightweight messaging bridge.

Contents
- `train.py` — training script that fits a LightGBM direction classifier from historical candles and saves model + scaler artifacts.
- `server.py` — a ZeroMQ REP server that loads the trained model, runs inference, and responds with an execution recommendation (BUY/SELL/HOLD) plus confidence and suggested stop/take-profit.
- `mt4_ea/AIBridge_EA.mq4` — MQL4 Expert Advisor template that packages recent candles to JSON and communicates with the Python server.
- `requirements.txt` — pinned Python dependencies for training and the serving process.

Important notes
- This repository is a technical template and is intended for development, testing, and education. It is not investment advice.
- Trading involves real financial risk. Always test strategies extensively in a demo account and use robust risk controls before any live deployment.
- The EA template includes placeholder calls for ZeroMQ; you must install and reference a compatible MQL4 ZeroMQ wrapper (for example, `mql4-zmq`) and adapt the EA to the wrapper's API.

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

Recommended next steps and pragmatic improvements

1) Productionize communications
	- Replace the EA's placeholder ZeroMQ calls with the actual wrapper API you install. Validate message formats and handle timeouts/failures deterministically.
	- Add a simple heartbeat or health-check message the EA can call periodically; the server should reply with status and model version.

2) Model lifecycle & reproducibility
	- Implement model versioning: store models with clear version tags or timestamps and log the active model version in both the server and EA logs.
	- Capture the preprocessing pipeline (scaler and feature transforms) alongside the model so training and serving are identical.

3) Testing and evaluation
	- Build a walk‑forward backtesting workflow that simulates fills, spread, and slippage using realistic order execution assumptions.
	- Maintain separate train/validation/test splits and evaluate strategies on out-of-sample windows to detect overfitting.

4) Risk and execution controls
	- Enforce trade safety rules in the EA: check spreads, maximum daily drawdown, and maximum concurrent exposure before sending orders.
	- Implement pip-accurate lot-sizing based on instrument tick/pip value (use broker contract specs) instead of simplified heuristics.
	- Log and persist all trade attempts, server responses, and errors for post-mortem analysis.

5) Operations and observability
	- Run the server as a managed service (Windows service or systemd unit) with automatic restart and log rotation.
	- Add structured logging and a small monitoring dashboard or alerts for server downtime, model errors, or unexpected latency.

6) Safety-first rollout
	- Start on a demo account and run an extended forward test before any live deployment. Gradually scale position sizes only after consistent, robust results.

These steps focus on engineering robustness and reproducibility; they are designed to reduce operational risk and make evaluation systematic.

Disclaimer
This repository is a technical template for integrating model inference with MT4. It is not financial, investment, or trading advice. Use the code and any derived strategies at your own risk. Always verify behavior on demo accounts and implement appropriate risk controls before trading with real capital.
