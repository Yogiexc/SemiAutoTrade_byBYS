import MetaTrader5 as mt5
from data_fetcher import fetch_multi_timeframe
import time
from datetime import datetime, timedelta

# =========================================================
# =========================================================
# TRADING MODE SELECTION
# Opsi 1: "HFT_PRO" (High Frequency Trading - Satset, Lot Berjenjang 5 Layer, Trailing 2 Pips)
# Opsi 2: "SWING_SAFE" (Aman, Cooldown 5 Menit, Max 3 Layer, Trailing 5 Pips)
# =========================================================
# Opsi 3: "TURBO_M1" (Sesi cepat ~1 jam di DEMO: filter longgar, cooldown 10 dtk, TP kecil/cepat, SL lebih ketat)
TRADING_MODE = "TURBO_M1"
TURBO = TRADING_MODE == "TURBO_M1"

def initialize_mt5():
    if not mt5.initialize():
        print(f"initialize() failed, error code = {mt5.last_error()}")
        return False
    print(f"MT5 Initialized Successfully: {mt5.version()}")
    return True

def evaluate_scalper_strategy(symbol: str, data: dict, open_positions: tuple, last_entry_time: float) -> tuple:
    """
    Sistem Skoring Confidence SCALPER (Total 100 Poin)
    - EMA Crossover M1 (30)
    - Trend M5 Searah (20)
    - Bollinger Bands M1 (20)
    - RSI M1 Fast (20)
    - Candlestick M1 (10)
    """
    df_m5 = data['M5']
    df_m1 = data['M1']
    
    from analyzer import detect_trend_fast, calculate_rsi, calculate_bollinger_bands, calculate_atr, check_session, get_spread, detect_candlestick_patterns, calculate_adx
    
    score_buy = 0
    score_sell = 0
    
    # 1. Trend Cepat M5 (20 Poin)
    m5_trend = detect_trend_fast(df_m5)
    if m5_trend == "BUY": score_buy += 20
    if m5_trend == "SELL": score_sell += 20
    
    # 2. EMA Crossover M1 (30 Poin)
    m1_trend = detect_trend_fast(df_m1)
    if m1_trend == "BUY": score_buy += 30
    if m1_trend == "SELL": score_sell += 30
    
    # 3. Bollinger Bands Momentum M1 (20 Poin)
    # Scalper mencari momentum saat harga menembus middle band ke atas/bawah
    up, mid, low = calculate_bollinger_bands(df_m1)
    current_price = df_m1['close'].iloc[-1]
    
    if current_price > mid.iloc[-1]: # Harga di atas rata-rata
        score_buy += 20
    if current_price < mid.iloc[-1]: # Harga di bawah rata-rata
        score_sell += 20
        
    # 4. RSI Fast M1 (10 Poin)
    # Mengukur kekuatan tren (Bukan overbought/oversold)
    rsi_m1 = calculate_rsi(df_m1, period=7).iloc[-1]
    if rsi_m1 > 60: score_buy += 10 # Momentum naik kuat
    if rsi_m1 < 40: score_sell += 10 # Momentum turun kuat
        
    # 4.5 ADX Trend Strength M1 (10 Poin)
    adx_m1 = calculate_adx(df_m1, period=14).iloc[-1]
    if adx_m1 > 25: 
        if m5_trend == "BUY": score_buy += 10
        elif m5_trend == "SELL": score_sell += 10
        
    # 5. Candlestick M1 (10 Poin)
    df_m1_candle = detect_candlestick_patterns(df_m1)
    current_candle = df_m1_candle['pattern'].iloc[-1]
    if current_candle in ["Hammer", "Bullish Engulfing"]: score_buy += 10
    if current_candle in ["Shooting Star", "Bearish Engulfing"]: score_sell += 10
    
    # Volatilitas (ATR) M1 untuk hitung SL/TP
    current_atr = calculate_atr(df_m1, period=14).iloc[-1]

    # TURBO: koreksi arah (EMA terlambat -> pakai posisi harga & momentum candle)
    if TURBO:
        from analyzer import calculate_ema
        ema9_m1 = calculate_ema(df_m1, 9).iloc[-1]
        closes = df_m1['close'].iloc[-4:].values
        opens = df_m1['open'].iloc[-4:].values
        last_body = df_m1['close'].iloc[-1] - df_m1['open'].iloc[-1]
        down_mom = all(closes[i] < closes[i-1] for i in range(1, len(closes)))
        up_mom = all(closes[i] > closes[i-1] for i in range(1, len(closes)))
        # Harga sudah di bawah EMA9 -> batalkan poin BUY dari EMA, beri SELL
        if current_price < ema9_m1:
            score_buy = max(0, score_buy - 30)
            score_sell += 15
        elif current_price > ema9_m1:
            score_sell = max(0, score_sell - 30)
            score_buy += 15
        if down_mom: score_sell += 15; score_buy = max(0, score_buy - 15)
        if up_mom: score_buy += 15; score_sell = max(0, score_sell - 15)
        # Candle terakhir besar berlawanan arah -> blokir
        if last_body < -current_atr: score_buy = 0
        if last_body > current_atr: score_sell = 0
        
    # === EVALUASI FINAL ===
    direction = "BUY" if score_buy > score_sell else "SELL"
    final_score = max(score_buy, score_sell)
    
    session_info = check_session()
    current_spread = get_spread(symbol)
    
    print("\n" + "="*40)
    print(f"[*] HFT SCALPER ANALYSIS : {symbol}")
    print("="*40)
    print(f"[Market] Session        : {session_info['session']}")
    print(f"[Market] Spread         : {current_spread:.1f} pips")
    print(f"[M5] Trend Direction    : {m5_trend}")
    print(f"[M1] Fast Crossover     : {m1_trend}")
    print(f"[M1] Current Price      : {current_price:.5f}")
    print(f"[M1] RSI (7)            : {rsi_m1:.2f}")
    print(f"[M1] ADX (14)           : {adx_m1:.2f}")
    print(f"[M1] Volatility (ATR)   : {current_atr:.5f}")
    print(f"[M1] Candlestick        : {current_candle}")
    
    recommendation = "WAIT"
    reasons = []
    
    from telegram_bot import send_telegram_message
    from risk_manager import check_max_positions, check_daily_loss, check_news_filter
    
    # HARD FILTERS
    if not session_info['can_trade'] and not TURBO:
        reasons.append(f"Di luar jam trading (Sesi: {session_info['session']})")
        
    batas_adx = 15 if TURBO else (20 if TRADING_MODE == "HFT_PRO" else 25)
    if adx_m1 < batas_adx:
        reasons.append(f"Sideways Detected! ADX rendah ({adx_m1:.2f} < {batas_adx}), Dilarang Entry!")
        
    # ANTI-PUCUK & ANTI-LEMBAH FILTER
    if direction == "BUY":
        if rsi_m1 > 70:
            reasons.append(f"Bahaya Pucuk! RSI sudah overbought ({rsi_m1:.2f} > 70). Dilarang BUY!")
        if current_candle in ["Shooting Star", "Bearish Engulfing"]:
            reasons.append(f"Bahaya Reversal! Muncul candle turun ({current_candle}). Dilarang BUY!")
    elif direction == "SELL":
        if rsi_m1 < 30:
            reasons.append(f"Bahaya Lembah! RSI sudah oversold ({rsi_m1:.2f} < 30). Dilarang SELL!")
        if current_candle in ["Hammer", "Bullish Engulfing"]:
            reasons.append(f"Bahaya Reversal! Muncul candle naik ({current_candle}). Dilarang SELL!")
        
    import time
    batas_cooldown = 10 if TURBO else (30 if TRADING_MODE == "HFT_PRO" else 300)
    if time.time() - last_entry_time < batas_cooldown: 
        waktu_tunggu = f"{batas_cooldown} Detik"
        reasons.append(f"Masih dalam masa Cooldown (Tunggu {waktu_tunggu} sejak open terakhir)")
        
    num_positions = len(open_positions) if open_positions else 0
    if num_positions > 0:
        last_pos_price = open_positions[-1].price_open
        point = mt5.symbol_info(symbol).point
        distance_points = abs(current_price - last_pos_price) / point
        min_distance = 20 if TURBO else (50 if TRADING_MODE == "HFT_PRO" else 200)
        if distance_points < min_distance: 
            reasons.append(f"Jarak dengan layer sebelumnya terlalu dekat ({distance_points:.0f} pts < {min_distance} pts)")
        
    # MAX SPREAD SCALPING
    # Dilonggarkan menjadi 50.0 pips khusus untuk akun Demo agar bot bisa menembak
    max_spread = 50.0 
    if current_spread > max_spread:
        reasons.append(f"Spread terlalu tinggi untuk Scalping ({current_spread:.1f} pips > {max_spread} pips)")
        
    # Risk Management Filters
    max_layers = 3 if TURBO else (5 if TRADING_MODE == "HFT_PRO" else 3)
    max_pos_check = check_max_positions(symbol, max_allowed=max_layers)
    if not max_pos_check["can_trade"]:
        reasons.append(max_pos_check["reason"])
        
    daily_loss_check = check_daily_loss(max_loss_percent=-50.0) # Dilonggarkan sementara untuk testing malam ini
    if not daily_loss_check["can_trade"]:
        reasons.append(daily_loss_check["reason"])
    
    if len(reasons) == 0:
        min_score_xau = 60 if TURBO else (70 if TRADING_MODE == "HFT_PRO" else 80)
        min_score_eur = 60 if TURBO else (70 if TRADING_MODE == "HFT_PRO" else 80)
        min_score = min_score_xau if symbol == "XAUUSD" else min_score_eur
        
        if final_score >= min_score: 
            recommendation = direction
        else:
            reasons.append(f"Confidence Score kurang ({final_score}% dibawah {min_score}%)")
            
    print("\n" + "="*40)
    print(f"[*] KESIMPULAN ALGORITMA : {recommendation} (Score: {final_score}%)")
    
    report = ""
    if recommendation != "WAIT":
        # SL/TP Diperlebar agar tidak tersentuh oleh spread
        # TURBO: TP dekat (cepat kena, win rate naik), SL lebih ketat
        sl_pips = (current_atr * 1.2) if TURBO else (current_atr * 3.0)
        tp_pips = (current_atr * 1.0) if TURBO else (current_atr * 6.0)
        
        sl_price = current_price - sl_pips if direction == "BUY" else current_price + sl_pips
        tp_price = current_price + tp_pips if direction == "BUY" else current_price - tp_pips
        
        print(f"[*] Arah Target     : {direction}")
        print(f"   Stop Loss   (SL) : {sl_price:.5f}")
        print(f"   Take Profit (TP) : {tp_price:.5f}")
        
        from telegram_formatter import format_target_acquired, format_position_opened
        
        report = format_target_acquired(symbol, direction, final_score, session_info['session'], current_spread)
        # Beri tag [SCALPER MODE]
        report = "[SCALPER MODE] ⚡\n" + report
        send_telegram_message(report)
        
        # Eksekusi Trading
        from executor import execute_trade
        
        # Dynamic Lot Sizing
        if TURBO:
            lot_sizes = [0.05, 0.03, 0.02]
            lot_to_use = lot_sizes[num_positions] if num_positions < len(lot_sizes) else 0.01
        elif TRADING_MODE == "HFT_PRO":
            lot_sizes = [0.05, 0.04, 0.03, 0.02, 0.01]
            lot_to_use = lot_sizes[num_positions] if num_positions < len(lot_sizes) else 0.01
        else:
            lot_sizes = [0.05, 0.03, 0.02]
            lot_to_use = lot_sizes[num_positions] if num_positions < len(lot_sizes) else 0.01
            
        success, ticket_or_err = execute_trade(symbol, direction, sl_price, tp_price, lot=lot_to_use)
        if success:
            open_reasons = [f"Trend M5 {m5_trend}", f"M1 Crossover {m1_trend}", f"ADX {adx_m1:.2f}"]
            pos_msg = format_position_opened(symbol, direction, lot_to_use, current_price, sl_price, tp_price, final_score, open_reasons, ticket_or_err)
            pos_msg = "[SCALPER MODE] ⚡\n" + pos_msg
            send_telegram_message(pos_msg)
            
            # Catat trade ke JSON untuk Performance Analyzer
            from performance_logger import log_trade_entry
            import uuid
            
            trend_h4 = detect_trend_fast(data['H4'])
            trend_h1 = detect_trend_fast(data['H1']) if 'H1' in data else "UNKNOWN"
            
            # 1. Trade ID UUID
            trade_id = "TRD-" + str(uuid.uuid4()).split("-")[0].upper()
            
            # 2. Market Regime
            if adx_m1 > 25: regime = "TRENDING"
            elif adx_m1 < 20: regime = "RANGING"
            else: regime = "VOLATILE"
            
            # 3. Account Balance & Equity
            acc_info = mt5.account_info()
            balance = acc_info.balance if acc_info else 0.0
            equity = acc_info.equity if acc_info else 0.0
            
            log_trade_entry(
                trade_id=trade_id, ticket=ticket_or_err, symbol=symbol, direction=direction, price=current_price,
                session=session_info['session'], spread=current_spread, score=final_score,
                rsi=rsi_m1, adx=adx_m1, atr=current_atr, trend_h4=trend_h4, trend_h1=trend_h1,
                candle=current_candle, strategy_version=TRADING_MODE + "_V1", market_regime=regime, 
                balance=balance, equity=equity, magic=888
            )
        else:
            send_telegram_message(f"❌ <b>EKSEKUSI GAGAL</b>\nRobot mencoba open posisi {direction} {symbol} tapi MT5 menolak. Error: {ticket_or_err}")
        
    else:
        print("[*] Alasan WAIT:")
        reason_text = "\n".join([f"- {r}" for r in reasons])
        print(reason_text)
        print(f"    (Buy Score: {score_buy}%, Sell Score: {score_sell}%)")

    print("="*40)
    return recommendation, report

if __name__ == "__main__":
    from telegram_bot import send_telegram_message
    from telegram_formatter import format_bot_online
    
    if initialize_mt5():
        symbols = ["EURUSD", "XAUUSD"]
        print(f"[*] Robot Scalper 24/7 diaktifkan. Memantau {len(symbols)} market setiap 10 DETIK...")
        
        from trade_manager import generate_overall_statistics
        stats_report = generate_overall_statistics(magic_number=888)
        print("\n" + stats_report + "\n")
        
        msg = format_bot_online()
        msg = msg.replace("Hedge Fund Sniper v2", "HFT Scalper Pro (M1)")
        send_telegram_message(msg)
        
        try:
            last_eval_time = 0
            last_entry_time = {"EURUSD": 0.0, "XAUUSD": 0.0}
            while True:
                # === MANAJEMEN TRANSAKSI AKTIF (Tiap 1 Detik) ===
                from trade_manager import manage_trailing_stops, auto_close_all
                from performance_logger import monitor_closed_trades
                
                # 0. Cek apakah ada trade yang tertutup untuk direkam ke CSV
                monitor_closed_trades(magic_number=888)
                
                # 1. Trailing Stop Khusus
                t_start = 2.0 if TRADING_MODE == "HFT_PRO" else 5.0
                t_step = 1.0 if TRADING_MODE == "HFT_PRO" else 2.0
                trailing_messages = manage_trailing_stops(magic_number=888, trailing_start_pips=t_start, trailing_step_pips=t_step)
                for t_msg in trailing_messages:
                    send_telegram_message(t_msg)
                    
                # 2. Auto Close (Take Profit / Cut Loss Darurat)
                # Hyper Scalper Brutal V3 (Max 3 Posisi): Lot 0.05. Target Cepat +$4.00, Max Loss -$20.00
                auto_close_messages = auto_close_all(magic_number=888, target_profit_usd=(2.0 if TURBO else 4.0), max_loss_usd=(-3.0 if TURBO else -20.0))
                for ac_msg in auto_close_messages:
                    send_telegram_message(ac_msg)
                    
                # === EVALUASI MARKET (Tiap 10 Detik) ===
                current_time = time.time()
                if current_time - last_eval_time >= (3 if TURBO else 10):
                    for symbol in symbols:
                        # Cek Max Pos
                        max_layers = 3 if TURBO else (5 if TRADING_MODE == "HFT_PRO" else 3)
                        open_positions = mt5.positions_get(symbol=symbol, magic=888)
                        if open_positions is not None and len(open_positions) >= max_layers:
                            continue
                            
                        multi_tf_data = fetch_multi_timeframe(symbol)
                        
                        if multi_tf_data:
                            open_positions_tuple = open_positions if open_positions else tuple()
                            last_time = last_entry_time.get(symbol, 0.0)
                            result, report_text = evaluate_scalper_strategy(symbol, multi_tf_data, open_positions_tuple, last_time)
                            
                            if result != "WAIT":
                                last_entry_time[symbol] = time.time()
                                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Signal {result} dieksekusi untuk {symbol}. Memulai Cooldown 5 menit.")
                            else:
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {symbol} Market belum ideal.")
                                if "DAILY LOSS LIMIT REACHED" in report_text:
                                    print("[*] Robot tidur sampai besok karena Daily Loss Limit!")
                                    now = datetime.now()
                                    tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
                                    sleep_seconds = (tomorrow - now).total_seconds()
                                    time.sleep(sleep_seconds)
                                    break 
                    
                    last_eval_time = time.time()
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitoring Profit (Aktif)...")
                    
                time.sleep(1) # Loop super cepat 1 detik
        except KeyboardInterrupt:
            print("\n[*] Bot dimatikan secara manual.")
        finally:
            mt5.shutdown()
