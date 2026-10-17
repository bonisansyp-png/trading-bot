"""
Unified Crypto Scalper & Disparity Monitor - Streamlit Dashboard
Visualizes real-time candlestick charts, BNF 25-MA disparity rates, order book liquidity depth,
and GRU neural price predictions.
"""
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import os

from config.settings import BotConfig
from core.indicators import Indicators
from core.gru_predictor import GRUPredictor

st.set_page_config(page_title="Unified Crypto Scalper & BNF Monitor", layout="wide")

st.title("⚡ Unified Crypto Scalper & BNF Disparity Engine")
st.caption("100% Python Algorithmic Trading Suite | Freqtrade + Hummingbot + Passivbot + Takashi Kotegawa Strategy")

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Configuration")
    symbol = st.selectbox("Trading Pair", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "DOGEUSDT"], index=0)
    interval = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "1h", "4h", "1d"], index=2)
    limit = st.slider("Historical Candles", min_value=100, max_value=500, value=200, step=50)
    enable_gru = st.checkbox("Enable GRU AI Forecast", value=True)

# Helper: Fetch Binance REST data
def fetch_klines(sym="BTCUSDT", tf="5m", count=200):
    url = f"https://api.binance.us/api/v3/klines?symbol={sym}&interval={tf}&limit={count}"
    res = requests.get(url)
    if res.status_code == 200:
        raw = res.json()
        df = pd.DataFrame(raw, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'tbb', 'tbq', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df[['open', 'high', 'low', 'close', 'volume']]
    return None

df = fetch_klines(symbol, interval, limit)

if df is not None:
    cfg = BotConfig()
    df = Indicators.calculate_all(df, cfg)
    last = df.iloc[-1]
    price = last['close']
    d25 = last.get('disparity_25', 0.0)

    # 1. Top Metrics Bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Live Price", f"${price:,.2f}")
    with col2:
        tag = "PANIC BUY ZONE" if d25 <= -5.0 else ("OVERHEATED" if d25 >= 7.5 else "NEUTRAL")
        st.metric("25-SMA Disparity (D25)", f"{d25:.2f}%", delta=tag)
    with col3:
        st.metric("RSI (14)", f"{last['rsi']:.1f}")
    with col4:
        st.metric("ATR (14)", f"${last['atr']:.2f}")

    # 2. BNF Panic Climax Alert
    if d25 <= -5.0:
        tp_low = price * 1.03
        tp_high = price * 1.07
        sl = price * 0.98
        st.error(f"🚨 **BNF PANIC DISPARITY BUY ACTIVE!** Price has plummeted {d25:.2f}% below the 25-MA. Target relief bounce: **${tp_low:,.2f} - ${tp_high:,.2f} (+3% to +7%)** | Rigid Stop: **${sl:,.2f} (-2%)** (0x margin, never average down).")

    # 3. Candlestick & Indicator Chart
    st.subheader(f"📊 {symbol} ({interval}) Live Market Structure")
    chart_df = df[['close', 'ema_fast', 'ema_medium', 'ema_slow', 'bb_upper', 'bb_lower']].tail(100)
    st.line_chart(chart_df)

    # 4. GRU Neural Price Prediction
    if enable_gru:
        st.subheader("🧠 Deep Learning GRU Forecast")
        gru = GRUPredictor()
        if gru.model is not None:
            pred = gru.predict_next_price(df)
            if pred is not None:
                diff = ((pred - price) / price) * 100
                st.info(f"GRU Forecast for next candle close: **${pred:,.2f}** ({'+' if diff > 0 else ''}{diff:.2f}% vs live price)")
            else:
                st.warning("Insufficient recent data to run GRU forecast.")
        else:
            st.warning("GRU model not loaded. (Place weights in models/crypto_gru_model.h5)")

else:
    st.error("Failed to fetch live market data from Binance.")
