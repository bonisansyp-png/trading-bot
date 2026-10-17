# Unified Crypto Scalper & BNF Disparity Trading Bot

**A unified, 100% Python algorithmic trading framework combining modern quantitative scalping with the legendary Takashi Kotegawa (BNF) mean-reversion strategy.**

---

## Key Capabilities

1. **Multi-Strategy Ensemble**:
   - **`KairiDisparityStrategy`**: BNF 25-period moving average disparity panic buy (capturing 3%–7% relief bounces with rigid stops and 0x/1x margin).
   - **`CryptoLaggardStrategy`**: BNF sector laggard rotation (*Junkan Busshoku*) detecting trailing peers when leaders surge.
   - **`EmaRsiAtrStrategy`**: Triple EMA crossover with ATR dynamic volatility bands.
   - **`MomentumScalperStrategy`**: Mean-reversion off Bollinger Bands (2σ) + MACD inflection.
   - **`GridScalperStrategy`**: Passivbot-inspired grid DCA around EMA.
   - **`OrderbookStrategy`**: Hummingbot-inspired top-10 level depth imbalance ($I > 0.60$).
   - **`CombinedStrategy`**: Consensus voting ensemble.

2. **Machine Learning Layer**:
   - 2-layer GRU Deep Learning forecaster (trained on 20-candle sequences of OHLCV).
   - Random Forest 5-bar directional classifier.

3. **High-Frequency Microstructure Feeds**:
   - Async WebSocket feeds with Volume-Weighted Mid-Price (VWMP) and 60-second trade flow delta aggregator.

4. **Industrial Risk Manager**:
   - Drawdown ceiling (5%), daily loss limit (3%), loss-streak cooldown (300s), and exponential anti-martingale size decay ($0.50^{\text{losses}}$).

---

## Quickstart Guide

### 1. Install Dependencies
```bash
cd unified-crypto-scalper
pip install -r requirements.txt
```

### 2. Run Paper Trading (Safe Mode)
```bash
python main.py paper
```

### 3. Run Live Trading (Real Money - Futures/Spot)
Configure `.env` with your CCXT API keys, then execute:
```bash
python main.py live
```

### 4. Launch the Streamlit Interactive Dashboard
```bash
streamlit run app_dashboard.py
```
