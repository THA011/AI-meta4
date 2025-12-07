"""
generate_sample.py
Creates a synthetic OHLCV CSV for testing train.py.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

n = 1000
start = datetime(2020,1,1)
dates = [start + timedelta(minutes=i) for i in range(n)]

np.random.seed(42)
price = 1.1000
prices = []
for i in range(n):
    price += np.random.normal(scale=0.0005)
    prices.append(price)

opens = [prices[i] for i in range(n)]
closes = [prices[i] + np.random.normal(scale=0.0002) for i in range(n)]
highs = [max(op,cl) + abs(np.random.normal(scale=0.0002)) for op,cl in zip(opens, closes)]
lows = [min(op,cl) - abs(np.random.normal(scale=0.0002)) for op,cl in zip(opens, closes)]
vol = np.random.randint(1, 100, size=n)

df = pd.DataFrame({
    'datetime': [d.strftime('%Y-%m-%d %H:%M:%S') for d in dates],
    'open': opens,
    'high': highs,
    'low': lows,
    'close': closes,
    'volume': vol,
})

import os
os.makedirs('f:/Projects/Python/mt4_agent/data', exist_ok=True)
path = 'f:/Projects/Python/mt4_agent/data/sample_candles.csv'
df.to_csv(path, index=False)
print('Wrote', path)
