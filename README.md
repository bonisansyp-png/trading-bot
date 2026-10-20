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

5. **Execution Quality**:
   - **Order State Machine**: Tracks pending → open → partial → filled → rejected/cancelled for every order.
   - **Retry with Exponential Backoff**: Auto-retries transient network/timeout errors (3 attempts, 500ms–5s backoff).
   - **Slippage Estimation**: Rejects market orders if estimated slippage from orderbook depth exceeds 0.3% default.
   - **Post-Only / Reduce-Only**: Configurable maker-only limit orders and reduce-only stop-losses to protect fees and position integrity.
   - **Paper Trading Realism**: Simulated latency (50ms), slippage (0.1%), partial fills (10% chance), and order rejects (2% chance).

---

## Execution Configuration (`config/settings.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `execution.max_order_retries` | 3 | Max retry attempts for transient errors |
| `execution.retry_backoff_base_ms` | 500 | Base backoff delay in milliseconds |
| `execution.retry_backoff_max_ms` | 5000 | Maximum backoff delay in milliseconds |
| `execution.slippage_model_enabled` | true | Enable orderbook-based slippage estimation |
| `execution.max_slippage_pct` | 0.003 | Reject orders if estimated slippage > 0.3% |
| `execution.slippage_depth_levels` | 10 | Orderbook depth levels for slippage calc |
| `execution.post_only` | false | Maker-only limit orders (no taker fees) |
| `execution.reduce_only_stops` | true | Stop-losses must be reduce-only |
| `execution.twap_enabled` | false | Enable TWAP order slicing |
| `execution.twap_slices` | 5 | Number of TWAP slices |
| `execution.twap_interval_sec` | 30 | Seconds between TWAP slices |
| `execution.paper_latency_ms` | 50 | Simulated network latency in paper mode |
| `execution.paper_slippage_pct` | 0.001 | Simulated slippage in paper mode (0.1%) |
| `execution.paper_partial_fill_chance` | 0.1 | Chance of partial fill in paper mode |
| `execution.paper_reject_chance` | 0.02 | Chance of order rejection in paper mode |

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
