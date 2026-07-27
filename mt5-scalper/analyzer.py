import pandas as pd
import numpy as np

def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
    """Menghitung Simple Moving Average"""
    return df[column].rolling(window=period).mean()

def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
    """Menghitung Exponential Moving Average"""
    return df[column].ewm(span=period, adjust=False).mean()

def detect_trend_fast(df: pd.DataFrame) -> str:
    """
    Deteksi trend sangat cepat menggunakan EMA 9 dan EMA 21.
    """
    if len(df) < 21:
        return "UNKNOWN"
        
    ema_9 = calculate_ema(df, 9)
    ema_21 = calculate_ema(df, 21)
    
    last_ema_9 = ema_9.iloc[-1]
    last_ema_21 = ema_21.iloc[-1]
    
    if last_ema_9 > last_ema_21:
        return "BUY"
    elif last_ema_9 < last_ema_21:
        return "SELL"
    else:
        return "SIDEWAY"

def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> tuple:
    """Menghitung Bollinger Bands (Upper, Mid, Lower)"""
    mid_band = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    upper_band = mid_band + (std_dev * std)
    lower_band = mid_band - (std_dev * std)
    return upper_band, mid_band, lower_band

def find_support_resistance(df: pd.DataFrame, window: int = 20) -> tuple:
    """
    Mencari titik support dan resistance terdekat dengan mencari
    nilai maximum dan minimum dalam rentang (window) tertentu.
    """
    if len(df) < window:
        return None, None
        
    recent_data = df.tail(window)
    resistance = recent_data['high'].max()
    support = recent_data['low'].min()
    return support, resistance

def detect_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mendeteksi pola candlestick tingkat lanjut:
    - Bullish/Bearish Engulfing
    - Hammer / Shooting Star (Pin Bar)
    - Doji
    - Inside Bar / Outside Bar
    """
    df = df.copy()
    df['pattern'] = 'None'
    
    for i in range(1, len(df)):
        curr_open = df['open'].iloc[i]
        curr_close = df['close'].iloc[i]
        curr_high = df['high'].iloc[i]
        curr_low = df['low'].iloc[i]
        
        prev_open = df['open'].iloc[i-1]
        prev_close = df['close'].iloc[i-1]
        prev_high = df['high'].iloc[i-1]
        prev_low = df['low'].iloc[i-1]
        
        body_size = abs(curr_close - curr_open)
        upper_wick = curr_high - max(curr_open, curr_close)
        lower_wick = min(curr_open, curr_close) - curr_low
        total_length = curr_high - curr_low
        
        # Doji
        if body_size <= (total_length * 0.1):
            df.loc[df.index[i], 'pattern'] = 'Doji'
            continue
            
        # Hammer / Bullish Pin Bar
        if lower_wick >= (2 * body_size) and upper_wick <= (0.5 * body_size):
            df.loc[df.index[i], 'pattern'] = 'Hammer'
            continue
            
        # Shooting Star / Bearish Pin Bar
        if upper_wick >= (2 * body_size) and lower_wick <= (0.5 * body_size):
            df.loc[df.index[i], 'pattern'] = 'Shooting Star'
            continue
        
        # Bullish Engulfing
        if (prev_close < prev_open) and (curr_close > curr_open) and (curr_close > prev_open) and (curr_open < prev_close):
            df.loc[df.index[i], 'pattern'] = 'Bullish Engulfing'
            continue
            
        # Bearish Engulfing
        if (prev_close > prev_open) and (curr_close < curr_open) and (curr_close < prev_open) and (curr_open > prev_close):
            df.loc[df.index[i], 'pattern'] = 'Bearish Engulfing'
            continue
            
        # Inside Bar
        if (curr_high < prev_high) and (curr_low > prev_low):
            df.loc[df.index[i], 'pattern'] = 'Inside Bar'
            continue
            
        # Outside Bar
        if (curr_high > prev_high) and (curr_low < prev_low):
            df.loc[df.index[i], 'pattern'] = 'Outside Bar'
            continue
            
    return df

def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """Menghitung Relative Strength Index (RSI)"""
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, column: str = 'close'):
    """Menghitung MACD, Signal Line, dan Histogram"""
    exp1 = df[column].ewm(span=fast, adjust=False).mean()
    exp2 = df[column].ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Menghitung Average True Range (ATR) untuk SL/TP dinamis"""
    high = df['high']
    low = df['low']
    close = df['close'].shift(1)
    
    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

import datetime
def check_session() -> dict:
    """
    Mengecek sesi pasar saat ini.
    Fokus: London (08:00 - 16:00 UTC) dan New York (13:00 - 21:00 UTC).
    Kita menggunakan waktu lokal (asumsi UTC+7 WIB).
    London: 15:00 - 23:00 WIB
    NY: 20:00 - 04:00 WIB (Next Day)
    """
    now = datetime.datetime.now()
    hour = now.hour
    weekday = now.weekday() # 0=Senin, 1=Selasa, ..., 5=Sabtu, 6=Minggu
    
    if weekday >= 5: # Sabtu & Minggu
        return {"can_trade": False, "session": "Weekend (Market Closed)"}
    
    is_london = 15 <= hour <= 23
    is_ny = (20 <= hour <= 23) or (0 <= hour <= 4)
    
    can_trade = is_london or is_ny
    session_name = "Asian/Sydney (NO TRADE)"
    if is_london and is_ny:
        session_name = "London & New York Overlap"
    elif is_london:
        session_name = "London"
    elif is_ny:
        session_name = "New York"
        
    return {"can_trade": can_trade, "session": session_name}

import MetaTrader5 as mt5
def get_spread(symbol: str) -> float:
    """
    Mendapatkan nilai spread saat ini dalam pips.
    """
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return 999.0
    
    # Menghitung pips
    point = symbol_info.point
    spread_points = symbol_info.spread
    
    # 1 pip = 10 points untuk broker 5 digit
    if point == 0.00001 or point == 0.001:
        return spread_points / 10.0
    return float(spread_points)

def detect_smc(df: pd.DataFrame, fractal_window: int = 5) -> dict:
    """
    Mendeteksi Smart Money Concepts (BOS, CHOCH, FVG).
    Mengembalikan dict berisi status SMC.
    """
    if len(df) < fractal_window * 2 + 1:
        return {"bos": "None", "choch": "None", "fvg": "None"}
        
    df = df.copy()
    
    # Deteksi FVG (Fair Value Gap) pada 3 candle terakhir
    # Index: -3 (Candle 1), -2 (Candle 2/Gap), -1 (Candle 3)
    fvg_status = "None"
    c1 = df.iloc[-3]
    c3 = df.iloc[-1]
    
    # Bullish FVG: Low candle 3 > High candle 1
    if c3['low'] > c1['high']:
        fvg_status = "Bullish FVG"
    # Bearish FVG: High candle 3 < Low candle 1
    elif c3['high'] < c1['low']:
        fvg_status = "Bearish FVG"
        
    # Deteksi Fractal (Swing High / Swing Low)
    # Sangat disederhanakan untuk mendeteksi BOS/CHOCH secara real-time
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    
    swing_highs = []
    swing_lows = []
    
    for i in range(fractal_window, len(df) - fractal_window):
        # Cek Swing High
        if all(highs[i] > highs[i-fractal_window:i]) and all(highs[i] > highs[i+1:i+fractal_window+1]):
            swing_highs.append(highs[i])
            
        # Cek Swing Low
        if all(lows[i] < lows[i-fractal_window:i]) and all(lows[i] < lows[i+1:i+fractal_window+1]):
            swing_lows.append(lows[i])
            
    bos_status = "None"
    choch_status = "None"
    
    current_close = closes[-1]
    
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        last_sh = swing_highs[-1]
        prev_sh = swing_highs[-2]
        last_sl = swing_lows[-1]
        prev_sl = swing_lows[-2]
        
        # Asumsi dasar Trend:
        is_uptrend = last_sh > prev_sh and last_sl > prev_sl
        is_downtrend = last_sh < prev_sh and last_sl < prev_sl
        
        # BOS Uptrend: Break Swing High terakhir
        if is_uptrend and current_close > last_sh:
            bos_status = "Bullish BOS"
        # BOS Downtrend: Break Swing Low terakhir
        elif is_downtrend and current_close < last_sl:
            bos_status = "Bearish BOS"
            
        # CHOCH Bearish: Harga mematahkan Swing Low terakhir saat Uptrend
        if is_uptrend and current_close < last_sl:
            choch_status = "Bearish CHOCH"
        # CHOCH Bullish: Harga mematahkan Swing High terakhir saat Downtrend
        elif is_downtrend and current_close > last_sh:
            choch_status = "Bullish CHOCH"
            
    return {
        "bos": bos_status,
        "choch": choch_status,
        "fvg": fvg_status
    }
