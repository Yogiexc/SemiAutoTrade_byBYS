import MetaTrader5 as mt5
import pandas as pd

def fetch_timeframe_data(symbol: str, timeframe: int, num_candles: int = 100) -> pd.DataFrame:
    """
    Mengambil data candlestick dari MT5 berdasarkan timeframe tertentu.
    """
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_candles)
    if rates is None:
        print(f"Failed to fetch data for {symbol} on TF {timeframe}")
        return pd.DataFrame()
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    # Membersihkan kolom yang tidak perlu
    df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume', 'real_volume']]
    return df

def fetch_multi_timeframe(symbol: str) -> dict:
    """
    Mengambil data untuk H4, H1, M30, M15, dan M5 sesuai dengan SOP Trading.
    """
    timeframes = {
        "H4": mt5.TIMEFRAME_H4,
        "H1": mt5.TIMEFRAME_H1,
        "M30": mt5.TIMEFRAME_M30,
        "M15": mt5.TIMEFRAME_M15,
        "M5": mt5.TIMEFRAME_M5
    }
    
    market_data = {}
    for tf_name, tf_val in timeframes.items():
        # Ambil 250 candle terakhir untuk masing-masing timeframe
        # Cukup untuk analisis trend (EMA 200), SNR, dan pola candlestick
        df = fetch_timeframe_data(symbol, tf_val, num_candles=250)
        market_data[tf_name] = df
        
    return market_data
