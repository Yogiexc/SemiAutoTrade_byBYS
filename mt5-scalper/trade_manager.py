import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd

def manage_trailing_stops(magic_number: int = 777, trailing_start_pips: float = 10.0, trailing_step_pips: float = 5.0):
    """
    Memindai semua posisi terbuka.
    Jika profit sudah mencapai trailing_start_pips, geser Stop Loss mengikuti harga saat ini.
    SL akan terus naik/turun (trailing) dengan jarak trailing_step_pips dari harga saat ini.
    """
    positions = mt5.positions_get(magic=magic_number)
    if positions is None or len(positions) == 0:
        return []
        
    messages = []
    
    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        order_type = pos.type
        price_open = pos.price_open
        price_current = pos.price_current
        sl_current = pos.sl
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            continue
            
        point = symbol_info.point
        point_to_pip = 10.0 if (point == 0.00001 or point == 0.001) else 1.0
        
        if order_type == mt5.ORDER_TYPE_BUY:
            profit_pips = (price_current - price_open) / (point * point_to_pip)
            if profit_pips >= trailing_start_pips:
                new_sl = price_current - (trailing_step_pips * point * point_to_pip)
                # Pastikan SL baru lebih tinggi dari SL lama (hanya bisa naik, tidak boleh turun)
                if new_sl > sl_current:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": ticket,
                        "symbol": symbol,
                        "sl": new_sl,
                        "tp": pos.tp
                    }
                    if mt5.order_send(request).retcode == mt5.TRADE_RETCODE_DONE:
                        msg = f"🔒 <b>TRAILING STOP NAIK!</b>\n\nPair : {symbol}\nProfit diamankan lebih tinggi!"
                        messages.append(msg)
                    
        elif order_type == mt5.ORDER_TYPE_SELL:
            profit_pips = (price_open - price_current) / (point * point_to_pip)
            if profit_pips >= trailing_start_pips:
                new_sl = price_current + (trailing_step_pips * point * point_to_pip)
                # Pastikan SL baru lebih rendah dari SL lama (hanya bisa turun, tidak boleh naik)
                # sl_current == 0.0 artinya belum pernah di set
                if new_sl < sl_current or sl_current == 0.0:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": ticket,
                        "symbol": symbol,
                        "sl": new_sl,
                        "tp": pos.tp
                    }
                    if mt5.order_send(request).retcode == mt5.TRADE_RETCODE_DONE:
                        msg = f"🔒 <b>TRAILING STOP TURUN!</b>\n\nPair : {symbol}\nProfit diamankan lebih rendah!"
                        messages.append(msg)
                    
    return messages

def generate_daily_report(magic_number: int = 777) -> str:
    """
    Men-generate laporan trading harian berdasarkan history MT5.
    """
    account_info = mt5.account_info()
    if account_info is None:
        return ""
        
    now = datetime.now()
    midnight = datetime(now.year, now.month, now.day)
    
    deals = mt5.history_deals_get(midnight, now)
    if deals is None:
        return ""
        
    # Filter deal khusus robot ini dan hanya entry OUT (Posisi Ditutup)
    # Di MT5, deal ENTRY_OUT adalah realisasi profit/loss
    bot_deals = [d for d in deals if d.magic == magic_number and d.entry == mt5.DEAL_ENTRY_OUT]
    
    if len(bot_deals) == 0:
        return "" # Tidak ada trade yang ditutup hari ini
        
    total_trades = len(bot_deals)
    win_trades = sum(1 for d in bot_deals if d.profit > 0)
    loss_trades = total_trades - win_trades
    
    win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0
    net_profit = sum(d.profit for d in bot_deals)
    
    # Hitung Best Pair
    pair_profits = {}
    for d in bot_deals:
        if d.symbol not in pair_profits:
            pair_profits[d.symbol] = 0
        pair_profits[d.symbol] += d.profit
    
    best_pair = max(pair_profits, key=pair_profits.get) if pair_profits else "-"
    
    date_str = now.strftime("%d %B %Y")
    
    report = (
        f"📊 <b>DAILY REPORT</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Tanggal :\n{date_str}\n\n"
        f"Trade :\n{total_trades}\n\n"
        f"Win :\n{win_trades}\n\n"
        f"Loss :\n{loss_trades}\n\n"
        f"Win Rate :\n{win_rate:.1f}%\n\n"
        f"Net Profit :\n+${net_profit:.2f}\n\n"
        f"Balance :\n${account_info.balance:.2f}\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    return report

def generate_overall_statistics(magic_number: int = 777) -> str:
    """
    Men-generate laporan statistik keseluruhan berdasarkan seluruh history MT5.
    """
    account_info = mt5.account_info()
    if account_info is None:
        return ""
        
    date_from = datetime(2020, 1, 1) # Ambil sejauh mungkin
    now = datetime.now()
    
    deals = mt5.history_deals_get(date_from, now)
    if deals is None:
        return "[-] Gagal mengambil history."
        
    bot_deals = [d for d in deals if d.magic == magic_number and d.entry == mt5.DEAL_ENTRY_OUT]
    
    if len(bot_deals) == 0:
        return "[-] Belum ada history trade untuk robot ini."
        
    total_trades = len(bot_deals)
    win_trades = []
    loss_trades = []
    
    for d in bot_deals:
        if d.profit > 0:
            win_trades.append(d.profit)
        elif d.profit < 0:
            loss_trades.append(d.profit)
            
    win_count = len(win_trades)
    loss_count = len(loss_trades)
    
    gross_profit = sum(win_trades)
    gross_loss = abs(sum(loss_trades))
    net_profit = sum(d.profit for d in bot_deals)
    
    win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
    avg_win = (gross_profit / win_count) if win_count > 0 else 0
    avg_loss = (gross_loss / loss_count) if loss_count > 0 else 0
    
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.9 if gross_profit > 0 else 0)
    expected_payoff = (net_profit / total_trades) if total_trades > 0 else 0
    
    report = (
        f"📈 STATISTIK KESELURUHAN (Magic: {magic_number})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Total Trade    : {total_trades}\n"
        f"Win            : {win_count}\n"
        f"Lose           : {loss_count}\n"
        f"Win Rate       : {win_rate:.1f}%\n"
        f"Average Win    : +${avg_win:.2f}\n"
        f"Average Loss   : -${avg_loss:.2f}\n"
        f"Profit Factor  : {profit_factor:.2f}\n"
        f"Expected Profit: {('+$' if expected_payoff >= 0 else '-$')}{abs(expected_payoff):.2f}/trade\n"
        f"Net Profit     : {('+$' if net_profit >= 0 else '-$')}{abs(net_profit):.2f}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    return report

def auto_close_all(magic_number: int = 777, target_profit_usd: float = 3.0, max_loss_usd: float = -10.0) -> list:
    """
    Menghitung total floating profit dari semua posisi yang dikelola robot.
    Jika total >= target_profit_usd atau <= max_loss_usd, TUTUP SEMUA.
    """
    positions = mt5.positions_get(magic=magic_number)
    if positions is None or len(positions) == 0:
        return []
        
    total_profit = sum(pos.profit for pos in positions)
    messages = []
    
    if total_profit >= target_profit_usd or total_profit <= max_loss_usd:
        reason = "TARGET PROFIT TERCAPAI" if total_profit >= target_profit_usd else "CUT LOSS DARURAT"
        
        # Tutup semua posisi
        for pos in positions:
            tick = mt5.symbol_info_tick(pos.symbol)
            if tick is None: continue
            
            close_price = tick.ask if pos.type == mt5.ORDER_TYPE_SELL else tick.bid
            action_type = mt5.ORDER_TYPE_BUY if pos.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": action_type,
                "position": pos.ticket,
                "price": close_price,
                "deviation": 20,
                "magic": magic_number,
                "comment": "AutoClose TP" if total_profit > 0 else "AutoClose SL",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            # Fallback filling type
            symbol_info = mt5.symbol_info(pos.symbol)
            if symbol_info.filling_mode & 2:
                request["type_filling"] = mt5.ORDER_FILLING_IOC
                
            result = mt5.order_send(request)
            if result is None:
                err = mt5.last_error()
                print(f"[-] GAGAL Auto-Close {pos.symbol}! Invalid Request: {err}")
            elif result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"[-] GAGAL Auto-Close {pos.symbol}! Error: {result.retcode}")
            else:
                print(f"[+] BERHASIL Auto-Close {pos.symbol} di harga {close_price}")
            
        sign = "+" if total_profit > 0 else ""
        msg = f"💥 <b>AUTO CLOSE TRIGGERED</b>\n\nSemua posisi ditutup secara otomatis!\nAlasan : {reason}\nTotal PnL : {sign}${total_profit:.2f}"
        messages.append(msg)
        
    return messages
