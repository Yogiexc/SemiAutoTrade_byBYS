import MetaTrader5 as mt5
from data_fetcher import fetch_multi_timeframe
from analyzer import (
    detect_trend, 
    find_support_resistance, 
    detect_candlestick_patterns,
    calculate_rsi,
    calculate_macd,
    calculate_atr
)
# from ai_engine import get_ai_analysis # Dimatikan sementara karena fokus ke Algo Trading

def initialize_mt5():
    if not mt5.initialize():
        print(f"initialize() failed, error code = {mt5.last_error()}")
        return False
    print(f"MT5 Initialized Successfully: {mt5.version()}")
    return True

def evaluate_sniper_strategy(symbol: str, data: dict) -> tuple:
    """
    Sistem Skoring Confidence (Total 100 Poin)
    - Trend H4 (20)
    - SMC: BOS/CHOCH/FVG di M15 (30)
    - RSI & MACD di M15 (20)
    - S/R Valid di H1 (15)
    - Candle & Volatility M5/M15 (15)
    """
    df_h4 = data['H4']
    df_h1 = data['H1']
    df_m15 = data['M15']
    df_m5 = data['M5']
    
    from analyzer import detect_trend, find_support_resistance, calculate_rsi, calculate_macd, calculate_atr, check_session, get_spread, detect_candlestick_patterns, detect_smc
    
    score_buy = 0
    score_sell = 0
    
    # 1. H4 Trend (20 Poin)
    h4_trend = detect_trend(df_h4)
    if h4_trend == "BUY": score_buy += 20
    if h4_trend == "SELL": score_sell += 20
    
    # 2. SMC M15 (30 Poin)
    smc_data = detect_smc(df_m15)
    has_bullish_smc = (smc_data['bos'] == "Bullish BOS") or (smc_data['choch'] == "Bullish CHOCH") or (smc_data['fvg'] == "Bullish FVG")
    has_bearish_smc = (smc_data['bos'] == "Bearish BOS") or (smc_data['choch'] == "Bearish CHOCH") or (smc_data['fvg'] == "Bearish FVG")
    
    if has_bullish_smc: score_buy += 30
    if has_bearish_smc: score_sell += 30
    
    # 3. RSI & MACD M15 (20 Poin)
    df_m15_rsi = calculate_rsi(df_m15)
    df_m15_macd, df_m15_signal, df_m15_hist = calculate_macd(df_m15)
    current_rsi = df_m15_rsi.iloc[-1]
    current_macd = df_m15_macd.iloc[-1]
    current_signal = df_m15_signal.iloc[-1]
    current_hist = df_m15_hist.iloc[-1]
    
    # RSI (10 Poin)
    if current_rsi < 35: score_buy += 10
    if current_rsi > 65: score_sell += 10
    
    # MACD (10 Poin)
    if current_macd > current_signal and current_hist > 0: score_buy += 10
    if current_macd < current_signal and current_hist < 0: score_sell += 10
    
    # 4. Support & Resistance H1 (15 Poin)
    sup, res = find_support_resistance(df_h1)
    current_price = df_m15['close'].iloc[-1]
    
    if sup and (current_price - sup) < 0.0020:
        score_buy += 15
    if res and (res - current_price) < 0.0020:
        score_sell += 15
        
    # 5. Candlestick & ATR (15 Poin)
    df_m5_candle = detect_candlestick_patterns(df_m5)
    current_candle = df_m5_candle['pattern'].iloc[-1]
    
    # Candle (10 Poin)
    if current_candle in ["Hammer", "Bullish Engulfing"]: score_buy += 10
    if current_candle in ["Shooting Star", "Bearish Engulfing"]: score_sell += 10
    
    # ATR Volatility (5 Poin)
    df_m15_atr = calculate_atr(df_m15)
    current_atr = df_m15_atr.iloc[-1]
    if current_atr > 0.0005:
        score_buy += 5
        score_sell += 5
        
    # === EVALUASI FINAL ===
    direction = "BUY" if score_buy > score_sell else "SELL"
    final_score = max(score_buy, score_sell)
    
    session_info = check_session()
    current_spread = get_spread(symbol)
    
    print("\n" + "="*40)
    print(f"[*] HEDGE FUND ALGO ANALYSIS : {symbol}")
    print("="*40)
    print(f"[Market] Session        : {session_info['session']}")
    print(f"[Market] Spread         : {current_spread:.1f} pips")
    print(f"[H4] Trend Direction    : {h4_trend}")
    if sup: print(f"[H1] Nearest Support    : {sup:.5f}")
    if res: print(f"[H1] Nearest Resistance : {res:.5f}")
    print(f"[M15] Current Price     : {current_price:.5f}")
    print(f"[M15] RSI (Momentum)    : {current_rsi:.2f}")
    print(f"[M15] MACD (Trend)      : {current_macd:.5f} (Signal: {current_signal:.5f})")
    print(f"[M15] Volatility (ATR)  : {current_atr:.5f}")
    print(f"[M5] Candlestick        : {current_candle}")
    print(f"[SMC] BOS               : {smc_data['bos']}")
    print(f"[SMC] CHOCH             : {smc_data['choch']}")
    print(f"[SMC] FVG               : {smc_data['fvg']}")
    
    recommendation = "WAIT"
    reasons = []
    
    from telegram_bot import send_telegram_message
    from risk_manager import check_max_positions, check_daily_loss, check_news_filter
    
    # HARD FILTERS
    if not session_info['can_trade']:
        reasons.append(f"Di luar jam trading (Sesi: {session_info['session']})")
        
    max_spread = 30.0 if symbol == "XAUUSD" else 2.5
    if current_spread > max_spread:
        reasons.append(f"Spread terlalu tinggi ({current_spread:.1f} pips diatas {max_spread} pips)")
        
    # Risk Management Filters
    max_pos_check = check_max_positions(symbol, max_allowed=2)
    if not max_pos_check["can_trade"]:
        reasons.append(max_pos_check["reason"])
        
    daily_loss_check = check_daily_loss(max_loss_percent=-50.0) # Dilonggarkan sementara untuk testing malam ini
    if not daily_loss_check["can_trade"]:
        reasons.append(daily_loss_check["reason"])
        
    news_check = check_news_filter(symbol)
    if not news_check["can_trade"]:
        reasons.append(news_check["reason"])
    
    if len(reasons) == 0:
        if final_score >= 85:
            recommendation = direction
        else:
            reasons.append(f"Confidence Score kurang ({final_score}% dibawah 85%)")
            
    print("\n" + "="*40)
    print(f"[*] KESIMPULAN ALGORITMA : {recommendation} (Score: {final_score}%)")
    
    report = ""
    if recommendation != "WAIT":
        sl_pips = (current_atr * 1.5)
        tp_pips = (current_atr * 3.0)
        
        sl_price = current_price - sl_pips if direction == "BUY" else current_price + sl_pips
        tp_price = current_price + tp_pips if direction == "BUY" else current_price - tp_pips
        
        print(f"[*] Arah Target     : {direction}")
        print(f"   Stop Loss   (SL) : {sl_price:.5f}")
        print(f"   Take Profit (TP) : {tp_price:.5f}")
        
        from telegram_formatter import format_target_acquired, format_position_opened
        
        # Kirim sinyal Target Acquired ke Telegram
        report = format_target_acquired(symbol, direction, final_score, session_info['session'], current_spread)
        send_telegram_message(report)
        
        # Eksekusi Trading
        from executor import execute_trade
        success, ticket_or_err = execute_trade(symbol, direction, sl_price, tp_price)
        if success:
            open_reasons = [f"Trend H4 {h4_trend}", "EMA Alignment", f"RSI {current_rsi:.2f}", "MACD Validated", "Support/Resist Validated"]
            pos_msg = format_position_opened(symbol, direction, 0.01, current_price, sl_price, tp_price, final_score, open_reasons, ticket_or_err)
            send_telegram_message(pos_msg)
        else:
            send_telegram_message(f"❌ <b>EKSEKUSI GAGAL</b>\nRobot mencoba open posisi {direction} {symbol} tapi MT5 menolak. Error: {ticket_or_err}")
        
    else:
        from telegram_formatter import format_monitoring_wait
        print("[*] Alasan WAIT:")
        reason_text = "\n".join([f"- {r}" for r in reasons])
        print(reason_text)
        print(f"    (Buy Score: {score_buy}%, Sell Score: {score_sell}%)")
        
        # Prepare WAIT report
        report = format_monitoring_wait(symbol, final_score, score_buy, score_sell, reasons)

    print("="*40)
    return recommendation, report

import time
from datetime import datetime, timedelta

if __name__ == "__main__":
    from telegram_bot import send_telegram_message
    from telegram_formatter import format_bot_online
    
    if initialize_mt5():
        symbols = ["EURUSD", "XAUUSD"]
        print(f"[*] Robot Sniper 24/7 diaktifkan. Memantau {len(symbols)} market setiap 1 menit...")
        
        # Send Online Message
        send_telegram_message(format_bot_online())
        
        try:
            first_loop = True
            report_sent_today = False # Penanda agar report tidak terkirim dua kali sehari
            
            while True:
                from trade_manager import manage_trailing_stops, generate_daily_report
                
                # 1. Trade Management (Trailing Stops)
                ts_messages = manage_trailing_stops()
                for msg in ts_messages:
                    send_telegram_message(msg)
                    print(f"[*] Trailing Stop Aktif: {msg}")
                    
                # 2. Daily Report Check (Jam 23:58)
                now = datetime.now()
                if now.hour == 23 and now.minute == 58:
                    if not report_sent_today:
                        daily_rep = generate_daily_report()
                        if daily_rep:
                            send_telegram_message(daily_rep)
                            print("[*] Laporan harian terkirim!")
                        report_sent_today = True
                else:
                    report_sent_today = False # Reset flag di luar jam 23:58
                
                for symbol in symbols:
                    multi_tf_data = fetch_multi_timeframe(symbol)
                    
                    if multi_tf_data:
                        # evaluate_sniper_strategy sekarang mereturn (recommendation, report)
                        result, report_text = evaluate_sniper_strategy(symbol, multi_tf_data)
                        
                        if result != "WAIT":
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Signal {result} dieksekusi untuk {symbol}. Menunggu 5 menit untuk cooldown.")
                            time.sleep(300) # Jeda 5 menit cooldown setelah trade
                        else:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {symbol} Market belum ideal.")
                            
                            # Cek apakah alasannya adalah Daily Loss
                            if "DAILY LOSS LIMIT REACHED" in report_text:
                                # Parse out the loss percent if possible, or just send generic
                                from telegram_formatter import format_risk_protection
                                import re
                                loss_match = re.search(r'Loss hari ini: ([\-\d\.]+)%', report_text)
                                loss_val = loss_match.group(1) if loss_match else "-3.0"
                                send_telegram_message(format_risk_protection(loss_val))
                                
                                print("[*] Robot tidur sampai besok karena Daily Loss Limit!")
                                
                                # Hitung detik sampai jam 00:00 besok
                                tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
                                sleep_seconds = (tomorrow - now).total_seconds()
                                time.sleep(sleep_seconds)
                                break # Keluar dari loop for symbol

                            if first_loop:
                                send_telegram_message(report_text)
                
                if first_loop:
                    first_loop = False
                
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cek lagi 1 menit...")
                time.sleep(60) # Cek setiap 1 menit
        except KeyboardInterrupt:
            print("\n[*] Bot dimatikan secara manual.")
        finally:
            mt5.shutdown()
