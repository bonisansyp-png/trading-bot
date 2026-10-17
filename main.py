"""
Unified Crypto Scalper & Disparity Bot - Main Entry Point
Integrates:
- Real-time technical scalping (Freqtrade / Jesse AI)
- High-frequency OrderBook microstructure & trade delta flow (Hummingbot)
- Anti-drawdown risk management & grid accumulation (Passivbot)
- Takashi Kotegawa (BNF) 25-Period Disparity (Kairi-ritsu) panic buying
- Deep learning GRU price trend validation
"""
import time
import logging
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table

from config.settings import BotConfig
from core.indicators import Indicators
from core.strategies import get_strategy, Signal
from core.exchange import ExchangeConnector, PaperExchange
from core.risk_manager import RiskManager
from core.gru_predictor import GRUPredictor

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/bot.log')
    ]
)
logger = logging.getLogger(__name__)


class UnifiedCryptoBot:
    def __init__(self, config=None):
        self.config = config or BotConfig()
        self.strategy = get_strategy(self.config)
        self.risk_manager = RiskManager(self.config)
        self.gru_predictor = GRUPredictor(
            model_path=self.config.strategy.gru_model_path,
            scaler_path=self.config.strategy.gru_scaler_path,
            lookback=self.config.strategy.gru_lookback
        )
        self.running = False
        self.cycle_count = 0

        if self.config.mode == "live":
            self.exchange = ExchangeConnector(self.config).connect()
        else:
            self.exchange = PaperExchange(self.config)

    def show_banner(self):
        console.print("[bold cyan]====================================================[/bold cyan]")
        console.print("[bold green]  UNIFIED CRYPTO SCALPER & DISPARITY BOT (100% PYTHON) [/bold green]")
        console.print("[bold cyan]====================================================[/bold cyan]")
        console.print(f"Mode: [yellow]{self.config.mode.upper()}[/yellow] | Strategy: [magenta]{self.config.strategy.active_strategy}[/magenta]")
        console.print(f"Symbols: {', '.join(self.config.scalping.symbols)}")
        console.print(f"Timeframe: {self.config.scalping.timeframe} | Leverage: {self.config.scalping.leverage}x")
        console.print(f"Disparity Period: {self.config.strategy.disparity_period} (Panic Thresh: {self.config.strategy.disparity_panic_threshold}%)")
        console.print("[bold cyan]----------------------------------------------------[/bold cyan]")

    def process_symbol(self, symbol: str):
        try:
            # 1. Fetch OHLCV
            df = self.exchange.fetch_ohlcv(symbol, self.config.scalping.timeframe, 200)
            if df is None or len(df) < 30:
                return

            # 2. Vectorized Indicators & Disparity
            df = Indicators.calculate_all(df, self.config)

            # 3. Strategy Evaluation
            setup = self.strategy.analyze(df)
            if setup.signal == Signal.HOLD:
                return

            # 4. Optional GRU Deep Learning Directional Filter
            if self.config.strategy.use_gru_filter and self.gru_predictor.model is not None:
                predicted_price = self.gru_predictor.predict_next_price(df)
                if predicted_price is not None:
                    curr_price = df['close'].iloc[-1]
                    if setup.signal == Signal.LONG and predicted_price < curr_price:
                        logger.info(f"[{symbol}] LONG signal filtered out by GRU forecast (${predicted_price:.2f} < ${curr_price:.2f})")
                        return
                    elif setup.signal == Signal.SHORT and predicted_price > curr_price:
                        logger.info(f"[{symbol}] SHORT signal filtered out by GRU forecast (${predicted_price:.2f} > ${curr_price:.2f})")
                        return

            # 5. Risk Governor Verification
            can_trade, reason = self.risk_manager.can_trade()
            if not can_trade:
                logger.info(f"[{symbol}] {setup.signal.value} rejected by RiskManager: {reason}")
                return

            # 6. Check existing positions (No Averaging Down)
            if self.exchange.get_position(symbol):
                return

            # 7. Position Sizing
            size = self.risk_manager.calculate_position_size(
                self.risk_manager.current_balance, setup.entry_price, setup.stop_loss
            )
            if size <= 0:
                return

            side = 'buy' if setup.signal == Signal.LONG else 'sell'
            logger.info(
                f"[{symbol}] [EXECUTE {setup.signal.value}] Strategy: {setup.strategy_name} | "
                f"Entry: ${setup.entry_price:.4f} | SL: ${setup.stop_loss:.4f} | "
                f"TP: ${setup.take_profit:.4f} | Size: {size:.6f} | Conf: {setup.confidence:.2f}"
            )

            # 8. Order Placement
            if self.config.mode == "live":
                self.exchange.set_leverage(symbol, self.config.scalping.leverage)
                self.exchange.create_market_order(symbol, side, size)
                opp_side = 'sell' if side == 'buy' else 'buy'
                self.exchange.create_stop_loss(symbol, opp_side, size, setup.stop_loss)
            else:
                self.exchange.create_market_order(symbol, side, size, {'price': setup.entry_price})

        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")

    def check_exits(self, symbol: str):
        try:
            pos = self.exchange.get_position(symbol)
            if not pos:
                return

            df = self.exchange.fetch_ohlcv(symbol, self.config.scalping.timeframe, 5)
            if df is None or len(df) == 0:
                return

            price = df.iloc[-1]['close']
            entry = float(pos.get('entryPrice', 0.0))
            side = pos.get('side', 'long')
            sc = self.config.scalping

            hit_tp = False
            hit_sl = False

            if side == 'long':
                hit_tp = price >= entry * (1 + sc.take_profit_pct)
                hit_sl = price <= entry * (1 - sc.stop_loss_pct)
                pnl = (price - entry) * float(pos.get('contracts', 0.0))
            else:
                hit_tp = price <= entry * (1 - sc.take_profit_pct)
                hit_sl = price >= entry * (1 + sc.stop_loss_pct)
                pnl = (entry - price) * float(pos.get('contracts', 0.0))

            if hit_tp or hit_sl:
                reason = "TAKE PROFIT" if hit_tp else "STOP LOSS"
                logger.info(f"[{symbol}] Closed {side.upper()} position: {reason} | PnL: ${pnl:.4f}")
                if self.config.mode == "live":
                    opp_side = 'sell' if side == 'long' else 'buy'
                    self.exchange.create_market_order(symbol, opp_side, float(pos.get('contracts', 0.0)))
                else:
                    self.exchange.close_position(symbol, price)
                self.risk_manager.record_trade(pnl, symbol)

        except Exception as e:
            logger.error(f"Error checking exits for {symbol}: {e}")

    def print_status(self):
        stats = self.risk_manager.get_stats()
        table = Table(title="[bold yellow]Unified Bot Live Telemetry[/bold yellow]")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        for k, v in stats.items():
            table.add_row(k.replace('_', ' ').title(), f"{v:.4f}" if isinstance(v, float) else str(v))
        table.add_row("Cycle Iteration", str(self.cycle_count))
        console.print(table)

    def run(self):
        self.show_banner()
        self.running = True
        logger.info("Bot execution cycle initialized!")

        try:
            while self.running:
                self.cycle_count += 1
                for sym in self.config.scalping.symbols:
                    self.check_exits(sym)
                    self.process_symbol(sym)

                if self.cycle_count % 10 == 0:
                    self.print_status()

                time.sleep(5)  # 5-second polling loop
        except KeyboardInterrupt:
            logger.info("Bot manually terminated by user.")
            self.print_status()


if __name__ == "__main__":
    mode = "paper"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    cfg = BotConfig()
    cfg.mode = mode
    bot = UnifiedCryptoBot(cfg)
    bot.run()
