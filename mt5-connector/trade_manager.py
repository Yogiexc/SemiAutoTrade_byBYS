import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd

def manage_trailing_stops(magic_number: int = 777, break_even_pips: float = 15.0):
    """
    Memindai semua posisi terbuka milik robot.
    Jika profit sudah mencapai break_even_pips, geser Stop Loss ke harga Entry.
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
        # Normalisasi point ke pip (asumsi broker 5 digit)
        point_to_pip = 10.0 if (point == 0.00001 or point == 0.001) else 1.0
        
        # Jarak profit saat ini dalam pips
        if order_type == mt5.ORDER_TYPE_BUY:
            profit_pips = (price_current - price_open) / (point * point_to_pip)
            # Jika profit > target dan SL masih di bawah harga entry (belum break even)
            if profit_pips >= break_even_pips and sl_current < price_open:
                new_sl = price_open + (2 * point * point_to_pip) # Break even + 2 pips
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": ticket,
                    "symbol": symbol,
                    "sl": new_sl,
                    "tp": pos.tp
                }
                result = mt5.order_send(request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    msg = f"🔒 <b>TRAILING STOP UPDATED</b>\n\nPair : {symbol}\n\nSL dipindahkan ke Break Even (Profit diamankan)."
                    messages.append(msg)
                    
        elif order_type == mt5.ORDER_TYPE_SELL:
            profit_pips = (price_open - price_current) / (point * point_to_pip)
            # Jika profit > target dan SL masih di atas harga entry (belum break even)
            if profit_pips >= break_even_pips and (sl_current > price_open or sl_current == 0.0):
                new_sl = price_open - (2 * point * point_to_pip) # Break even + 2 pips
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": ticket,
                    "symbol": symbol,
                    "sl": new_sl,
                    "tp": pos.tp
                }
                result = mt5.order_send(request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    msg = f"🔒 <b>TRAILING STOP UPDATED</b>\n\nPair : {symbol}\n\nSL dipindahkan ke Break Even (Profit diamankan)."
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
        f"Best Pair :\n{best_pair}\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    return report
