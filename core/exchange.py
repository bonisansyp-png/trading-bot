"""
Unified Exchange Connector & Paper Trading Simulator
Supports CCXT live futures/spot connectivity as well as offline paper trading.
"""
import ccxt
import pandas as pd
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ExchangeConnector:
    def __init__(self, config):
        self.config = config
        self.exchange = None

    def connect(self):
        ec = self.config.exchange
        exchange_class = getattr(ccxt, ec.name, ccxt.binance)
        params = {
            'apiKey': ec.api_key,
            'secret': ec.api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        }
        if ec.testnet:
            params['sandbox'] = True
        self.exchange = exchange_class(params)
        logger.info(f"Connected to {ec.name} (sandbox={ec.testnet})")
        return self

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 200) -> pd.DataFrame:
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    def fetch_orderbook(self, symbol: str, limit: int = 10) -> Dict:
        return self.exchange.fetch_order_book(symbol, limit)

    def fetch_balance(self) -> Dict:
        return self.exchange.fetch_balance()

    def get_position(self, symbol: str) -> Optional[Dict]:
        try:
            positions = self.exchange.fetch_positions([symbol])
            for pos in positions:
                if pos['symbol'] == symbol and float(pos.get('contracts', 0)) > 0:
                    return pos
        except Exception as e:
            logger.error(f"Error fetching position for {symbol}: {e}")
        return None

    def set_leverage(self, symbol: str, leverage: int):
        try:
            self.exchange.set_leverage(leverage, symbol)
        except Exception as e:
            logger.warning(f"Leverage error on {symbol}: {e}")

    def create_market_order(self, symbol: str, side: str, amount: float, params: dict = None):
        return self.exchange.create_order(symbol, 'market', side, amount, None, params or {})

    def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params: dict = None):
        return self.exchange.create_order(symbol, 'limit', side, amount, price, params or {})

    def create_stop_loss(self, symbol: str, side: str, amount: float, stop_price: float):
        params = {'stopPrice': stop_price, 'reduceOnly': True}
        return self.exchange.create_order(symbol, 'stop_market', side, amount, None, params)

    def cancel_all_orders(self, symbol: str):
        self.exchange.cancel_all_orders(symbol)


class PaperExchange:
    def __init__(self, config):
        self.config = config
        self.balance = config.scalping.initial_capital
        self.positions: Dict[str, Dict] = {}
        self.trade_history: list = []
        self.order_id = 0

    def fetch_balance(self) -> Dict:
        return {'USDT': {'free': self.balance, 'total': self.balance}}

    def get_position(self, symbol: str) -> Optional[Dict]:
        return self.positions.get(symbol)

    def set_leverage(self, symbol: str, leverage: int):
        pass

    def create_market_order(self, symbol: str, side: str, amount: float, params: dict = None) -> Dict:
        self.order_id += 1
        price = params.get('price', 0.0) if params else 0.0
        order = {
            'id': f"paper_{self.order_id}",
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'status': 'closed',
            'timestamp': datetime.now().isoformat()
        }
        if side in ['buy', 'long']:
            self.positions[symbol] = {
                'symbol': symbol,
                'side': 'long',
                'contracts': amount,
                'entryPrice': price,
                'timestamp': datetime.now().isoformat()
            }
        else:
            self.positions[symbol] = {
                'symbol': symbol,
                'side': 'short',
                'contracts': amount,
                'entryPrice': price,
                'timestamp': datetime.now().isoformat()
            }
        self.trade_history.append(order)
        return order

    def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        pos = self.positions.pop(symbol, None)
        if not pos:
            return None
        entry = pos['entryPrice']
        amt = pos['contracts']
        side = pos['side']
        pnl = (exit_price - entry) * amt if side == 'long' else (entry - exit_price) * amt
        self.balance += pnl
        return pnl
