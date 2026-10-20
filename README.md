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
   - **Portfolio Heat**: Per-symbol notional exposure cap (5% default) and total portfolio heat cap (20% default) to prevent over-concentration.
   - **Volatility-Adjusted Sizing**: ATR-normalized risk per trade instead of flat capital %, scaling position size to market volatility.
   - **Circuit Breakers**: Automatic trading halt on flash-crash drawdown (2% in 15 min default) or consecutive exchange error streaks (5 default).
   - **Trailing Stop & Breakeven**: Auto-arm breakeven stop at 1.5% profit, then trail at 1% below high-water mark (long) / above (short).

---

## Risk Configuration (`config/settings.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `risk.max_daily_loss_pct` | 0.03 | Halt trading if daily PnL drops below -3% of capital |
| `risk.max_drawdown_pct` | 0.05 | Halt trading if peak-to-current drawdown exceeds 5% |
| `risk.max_consecutive_losses` | 5 | Pause after N straight losing trades |
| `risk.daily_trade_limit` | 50 | Maximum trades per day |
| `risk.max_position_size_pct` | 0.10 | Max capital allocated to a single trade |
| `risk.max_position_per_symbol_pct` | 0.05 | Max notional exposure per symbol |
| `risk.max_portfolio_heat_pct` | 0.20 | Max total notional exposure across all symbols |
| `risk.reduce_size_on_loss` | true | Exponentially reduce size after consecutive losses |
| `risk.vol_adjust_sizing` | true | Scale position size by ATR-based volatility |
| `risk.circuit_breaker_enabled` | true | Auto-halt on rapid drawdown or error streaks |
| `risk.circuit_breaker_drawdown_pct` | 0.02 | Flash-crash threshold (2% in window) |
| `risk.circuit_breaker_time_window_min` | 15 | Circuit breaker observation window |
| `risk.circuit_breaker_error_streak` | 5 | Consecutive exchange errors that trigger halt |
| `risk.trailing_stop_enabled` | true | Enable trailing stop after breakeven |
| `risk.trailing_stop_activation_pct` | 0.015 | Profit threshold to arm breakeven (1.5%) |
| `risk.trailing_stop_pct` | 0.01 | Trailing distance from high-water mark (1%) |
| `risk.breakeven_activation_pct` | 0.01 | Same as trailing_stop_activation_pct |

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
