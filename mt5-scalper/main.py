import MetaTrader5 as mt5
from data_fetcher import fetch_multi_timeframe
import time
from datetime import datetime, timedelta

def initialize_mt5():
    if not mt5.initialize():
        print(f"initialize() failed, error code = {mt5.last_error()}")
        return False
    print(f"MT5 Initialized Successfully: {mt5.version()}")
    return True

def evaluate_scalper_strategy(symbol: str, data: dict) -> tuple:
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
    
    from analyzer import detect_trend_fast, calculate_rsi, calculate_bollinger_bands, calculate_atr, check_session, get_spread, detect_candlestick_patterns
    
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
    
    # 3. Bollinger Bands M1 (20 Poin)
    # Scalper suka memantul dari lower band atau upper band
    up, mid, low = calculate_bollinger_bands(df_m1)
    current_price = df_m1['close'].iloc[-1]
    
    if current_price <= low.iloc[-1] + 0.00010: # Dekat lower band
        score_buy += 20
    if current_price >= up.iloc[-1] - 0.00010: # Dekat upper band
        score_sell += 20
        
    # 4. RSI Fast M1 (20 Poin)
    # Menggunakan period 7 untuk pergerakan liar
    rsi_m1 = calculate_rsi(df_m1, period=7).iloc[-1]
    if rsi_m1 < 30: score_buy += 20
    if rsi_m1 > 70: score_sell += 20
        
    # 5. Candlestick M1 (10 Poin)
    df_m1_candle = detect_candlestick_patterns(df_m1)
    current_candle = df_m1_candle['pattern'].iloc[-1]
    if current_candle in ["Hammer", "Bullish Engulfing"]: score_buy += 10
    if current_candle in ["Shooting Star", "Bearish Engulfing"]: score_sell += 10
    
    # Volatilitas (ATR) M1 untuk hitung SL/TP
    current_atr = calculate_atr(df_m1, period=14).iloc[-1]
        
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
    print(f"[M1] Volatility (ATR)   : {current_atr:.5f}")
    print(f"[M1] Candlestick        : {current_candle}")
    
    recommendation = "WAIT"
    reasons = []
    
    from telegram_bot import send_telegram_message
    from risk_manager import check_max_positions, check_daily_loss, check_news_filter
    
    # HARD FILTERS
    if not session_info['can_trade']:
        reasons.append(f"Di luar jam trading (Sesi: {session_info['session']})")
        
    # MAX SPREAD SCALPING (SANGAT KETAT)
    max_spread = 1.0 # Maksimal spread hanya 1.0 pip untuk scalping!
    if current_spread > max_spread:
        reasons.append(f"Spread terlalu tinggi untuk Scalping ({current_spread:.1f} pips > {max_spread} pips)")
        
    # Risk Management Filters
    max_pos_check = check_max_positions(symbol, max_allowed=5)
    if not max_pos_check["can_trade"]:
        reasons.append(max_pos_check["reason"])
        
    daily_loss_check = check_daily_loss(max_loss_percent=-3.0)
    if not daily_loss_check["can_trade"]:
        reasons.append(daily_loss_check["reason"])
    
    if len(reasons) == 0:
        if final_score >= 80: # Sedikit lebih agresif dari Sniper
            recommendation = direction
        else:
            reasons.append(f"Confidence Score kurang ({final_score}% dibawah 80%)")
            
    print("\n" + "="*40)
    print(f"[*] KESIMPULAN ALGORITMA : {recommendation} (Score: {final_score}%)")
    
    report = ""
    if recommendation != "WAIT":
        # SL/TP Sangat Sempit untuk Scalping
        sl_pips = (current_atr * 1.0)
        tp_pips = (current_atr * 2.0)
        
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
        success, ticket_or_err = execute_trade(symbol, direction, sl_price, tp_price)
        if success:
            open_reasons = [f"Trend M5 {m5_trend}", f"M1 Crossover {m1_trend}", f"RSI {rsi_m1:.2f}"]
            pos_msg = format_position_opened(symbol, direction, 0.01, current_price, sl_price, tp_price, final_score, open_reasons, ticket_or_err)
            pos_msg = "[SCALPER MODE] ⚡\n" + pos_msg
            send_telegram_message(pos_msg)
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
        
        msg = format_bot_online()
        msg = msg.replace("Hedge Fund Sniper v2", "HFT Scalper Pro (M1)")
        send_telegram_message(msg)
        
        try:
            first_loop = True
            while True:
                from trade_manager import manage_trailing_stops
                
                # Trailing Stops Scalper: BE sangat dekat (misal 5 pips)
                # Magic Number Scalper adalah 888
                ts_messages = manage_trailing_stops(magic_number=888, break_even_pips=5.0)
                for msg in ts_messages:
                    send_telegram_message("[SCALPER MODE] " + msg)
                    print(f"[*] Trailing Stop Aktif: {msg}")
                    
                for symbol in symbols:
                    multi_tf_data = fetch_multi_timeframe(symbol)
                    
                    if multi_tf_data:
                        result, report_text = evaluate_scalper_strategy(symbol, multi_tf_data)
                        
                        if result != "WAIT":
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Signal {result} dieksekusi untuk {symbol}. Menunggu 1 menit cooldown.")
                            time.sleep(60) # Cooldown hanya 1 menit
                        else:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {symbol} Market belum ideal.")
                            if "DAILY LOSS LIMIT REACHED" in report_text:
                                print("[*] Robot tidur sampai besok karena Daily Loss Limit!")
                                now = datetime.now()
                                tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
                                sleep_seconds = (tomorrow - now).total_seconds()
                                time.sleep(sleep_seconds)
                                break 
                
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cek lagi 10 detik...")
                time.sleep(10) # Cek setiap 10 detik
        except KeyboardInterrupt:
            print("\n[*] Bot dimatikan secara manual.")
        finally:
            mt5.shutdown()
