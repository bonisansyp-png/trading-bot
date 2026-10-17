"""
Unified Indicators Engine
Combines standard technical oscillators with the BNF 25-Day Disparity (Kairi-ritsu) indicator.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict


class Indicators:
    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        return series.rolling(window=period).mean()

    @staticmethod
    def disparity(series: pd.Series, period: int = 25) -> pd.Series:
        """BNF Moving Average Disparity (Kairi-ritsu / 乖離率)"""
        sma = series.rolling(window=period).mean()
        return ((series - sma) / sma) * 100.0

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def stochastic_rsi(series: pd.Series, period: int = 14,
                       smooth_k: int = 3, smooth_d: int = 3) -> Tuple[pd.Series, pd.Series]:
        rsi = Indicators.rsi(series, period)
        min_rsi = rsi.rolling(period).min()
        max_rsi = rsi.rolling(period).max()
        stoch = ((rsi - min_rsi) / (max_rsi - min_rsi + 1e-10)) * 100
        k = stoch.rolling(smooth_k).mean()
        d = k.rolling(smooth_d).mean()
        return k, d

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series,
            period: int = 14) -> pd.Series:
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.ewm(alpha=1/period, min_periods=period).mean()

    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26,
             signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = Indicators.ema(series, fast)
        ema_slow = Indicators.ema(series, slow)
        macd_line = ema_fast - ema_slow
        signal_line = Indicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20,
                        std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        middle = Indicators.sma(series, period)
        std_dev = series.rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return upper, middle, lower

    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series,
             volume: pd.Series) -> pd.Series:
        typical_price = (high + low + close) / 3
        cum_tp_vol = (typical_price * volume).cumsum()
        cum_vol = volume.cumsum()
        return cum_tp_vol / (cum_vol + 1e-10)

    @staticmethod
    def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
        return volume.rolling(window=period).mean()

    @staticmethod
    def momentum(series: pd.Series, period: int = 10) -> pd.Series:
        return series.pct_change(periods=period) * 100

    @staticmethod
    def orderbook_imbalance(bids: list, asks: list, depth: int = 10) -> float:
        bid_vol = sum([b[1] for b in bids[:depth]])
        ask_vol = sum([a[1] for a in asks[:depth]])
        total = bid_vol + ask_vol
        if total == 0:
            return 0.0
        return (bid_vol - ask_vol) / total

    @staticmethod
    def calculate_all(df: pd.DataFrame, config) -> pd.DataFrame:
        c = config.strategy
        df = df.copy()
        df['ema_fast'] = Indicators.ema(df['close'], c.ema_fast)
        df['ema_medium'] = Indicators.ema(df['close'], c.ema_medium)
        df['ema_slow'] = Indicators.ema(df['close'], c.ema_slow)
        df['rsi'] = Indicators.rsi(df['close'], c.rsi_period)
        df['stoch_k'], df['stoch_d'] = Indicators.stochastic_rsi(df['close'])
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], c.atr_period)
        df['macd'], df['macd_signal'], df['macd_hist'] = Indicators.macd(
            df['close'], c.macd_fast, c.macd_slow, c.macd_signal)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = Indicators.bollinger_bands(
            df['close'], c.bb_period, c.bb_std)
        df['vol_sma'] = Indicators.volume_sma(df['volume'], c.volume_sma_period)
        df['momentum'] = Indicators.momentum(df['close'])
        df['disparity_25'] = Indicators.disparity(df['close'], getattr(c, 'disparity_period', 25))
        if 'volume' in df.columns:
            df['vwap'] = Indicators.vwap(df['high'], df['low'], df['close'], df['volume'])
        return df
