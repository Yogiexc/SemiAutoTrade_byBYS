import os
import json
import csv
import MetaTrader5 as mt5
from datetime import datetime

ACTIVE_TRADES_FILE = "active_trades.json"
CSV_FILE = "performance_history.csv"

# Kolom-kolom yang akan dicatat di CSV
CSV_HEADERS = [
    "Trade_ID", "Date", "Ticket", "Symbol", "Type", "Session", "Spread_Cat", 
    "Score", "Trend_H4", "Trend_H1", "RSI", "ADX", "ATR", "Candle", 
    "Strategy_Version", "Market_Regime", "Balance", "Equity", 
    "Entry_Price", "Exit_Price", "MAE", "MFE", "Profit", 
    "Holding_Time_Seconds", "Exit_Reason", "Magic_Number"
]

def log_trade_entry(trade_id: str, ticket: int, symbol: str, direction: str, price: float, 
                    session: str, spread: float, score: float, 
                    rsi: float, adx: float, atr: float, trend_h4: str, trend_h1: str,
                    candle: str, strategy_version: str, market_regime: str,
                    balance: float, equity: float, magic: int = 888):
    """
    Menyimpan konteks trade yang baru dibuka ke dalam JSON sementara.
    """
    data = {}
    if os.path.exists(ACTIVE_TRADES_FILE):
        try:
            with open(ACTIVE_TRADES_FILE, "r") as f:
                data = json.load(f)
        except:
            pass
            
    # Kategori Spread
    spread_cat = "NORMAL"
    if spread < 10: spread_cat = "LOW"
    elif spread > 25: spread_cat = "HIGH"
            
    # Simpan konteks
    data[str(ticket)] = {
        "Ticket": ticket,
        "Symbol": symbol,
        "Type": direction,
        "Entry_Time_Unix": datetime.now().timestamp(),
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Entry_Price": price,
        "Session": session,
        "Trade_ID": trade_id,
        "Spread_Cat": spread_cat,
        "Score": score,
        "Trend_H4": trend_h4,
        "Trend_H1": trend_h1,
        "RSI": rsi,
        "ADX": adx,
        "ATR": atr,
        "Candle": candle,
        "Strategy_Version": strategy_version,
        "Market_Regime": market_regime,
        "Balance": balance,
        "Equity": equity,
        "Magic_Number": magic,
        "MAE": 0.0,  # Max Adverse Excursion
        "MFE": 0.0   # Max Favorable Excursion
    }
    
    with open(ACTIVE_TRADES_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
    print(f"[Logger V2] Trade {ticket} direkam dengan metrik Institusi.")

def monitor_closed_trades(magic_number: int = 888):
    """
    Update MAE/MFE & Cek trade tertutup.
    """
    if not os.path.exists(ACTIVE_TRADES_FILE):
        return
        
    try:
        with open(ACTIVE_TRADES_FILE, "r") as f:
            active_trades = json.load(f)
    except:
        return
        
    if not active_trades:
        return
        
    # Ambil posisi yang saat ini sedang floating di MT5
    positions = mt5.positions_get(magic=magic_number)
    if positions is None:
        # MT5 gagal membalas: jangan anggap semua trade tertutup (hindari baris palsu di CSV)
        return
    open_pos_dict = {str(pos.ticket): pos for pos in positions}
    
    closed_tickets = []
    json_updated = False
    
    now = datetime.now()
    
    # Ambil deals history 7 hari terakhir untuk cek closed trade
    # Mulai dari entry trade tertua yang masih aktif (bukan fixed 7 hari),
    # supaya trade yang ditutup saat bot mati tetap ketemu deal-nya.
    oldest_entry = min((c.get("Entry_Time_Unix", now.timestamp()) for c in active_trades.values()), default=now.timestamp())
    from_date = datetime.fromtimestamp(oldest_entry - 3600)
    history_deals = mt5.history_deals_get(from_date, now)
    
    for str_ticket, ctx in active_trades.items():
        if str_ticket in open_pos_dict:
            # UPDATE MAE & MFE
            pos = open_pos_dict[str_ticket]
            current_profit = pos.profit
            
            # Update MFE (Max Profit)
            if current_profit > ctx.get("MFE", 0.0):
                ctx["MFE"] = current_profit
                json_updated = True
                
            # Update MAE (Max Minus/Loss) - Semakin minus semakin dalam
            if current_profit < ctx.get("MAE", 0.0):
                ctx["MAE"] = current_profit
                json_updated = True
                
        else:
            # TRADE SUDAH DITUTUP
            ticket_int = int(str_ticket)
            
            exit_price = 0.0
            profit = 0.0
            exit_reason = "Unknown"
            
            if history_deals:
                for deal in history_deals:
                    if deal.position_id == ticket_int and deal.entry == mt5.DEAL_ENTRY_OUT:
                        exit_price = deal.price
                        profit = deal.profit + deal.commission + deal.swap
                        
                        # Infer Exit Reason dari Comment Broker
                        comment = deal.comment.lower() if deal.comment else ""
                        if "sl" in comment:
                            exit_reason = "SL"
                        elif "tp" in comment:
                            exit_reason = "TP"
                        elif "autoclose" in comment:
                            if profit > 0: exit_reason = "AutoClose Target"
                            else: exit_reason = "AutoClose CutLoss"
                        else:
                            if profit > 0: exit_reason = "Manual / Target"
                            else: exit_reason = "Manual / CutLoss"
                            
                        # Deteksi Trailing Stop (Biasa tertutup sebagai SL tapi profit > 0)
                        if exit_reason == "SL" and profit > 0:
                            exit_reason = "Trailing Stop"
                            
                        break
                        
            holding_time = now.timestamp() - ctx.get("Entry_Time_Unix", now.timestamp())
            
            # Tulis ke CSV
            if not os.path.exists(CSV_FILE):
                with open(CSV_FILE, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(CSV_HEADERS)
                    
            row = [
                ctx.get("Trade_ID", "UNKNOWN"), ctx.get("Date"), ctx.get("Ticket"), 
                ctx.get("Symbol"), ctx.get("Type"), ctx.get("Session"), 
                ctx.get("Spread_Cat"), ctx.get("Score"),
                ctx.get("Trend_H4", "-"), ctx.get("Trend_H1", "-"), 
                round(ctx.get("RSI", 0), 2), round(ctx.get("ADX", 0), 2), 
                round(ctx.get("ATR", 0), 5), ctx.get("Candle"), 
                ctx.get("Strategy_Version", "V2.x"), ctx.get("Market_Regime", "-"),
                round(ctx.get("Balance", 0.0), 2), round(ctx.get("Equity", 0.0), 2),
                ctx.get("Entry_Price"), exit_price, round(ctx.get("MAE", 0.0), 2), 
                round(ctx.get("MFE", 0.0), 2), round(profit, 2), 
                round(holding_time, 1), exit_reason, ctx.get("Magic_Number")
            ]
            
            try:
                with open(CSV_FILE, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(row)
                print(f"[Logger V2] Trade {str_ticket} ditutup ({exit_reason}). MAE: {ctx.get('MAE',0):.2f}, MFE: {ctx.get('MFE',0):.2f}, PnL: ${profit:.2f}")
            except Exception as e:
                print(f"[Logger V2] Error CSV: {e}")
                
            closed_tickets.append(str_ticket)
            
    # Hapus dari JSON dan simpan update MAE/MFE
    if closed_tickets or json_updated:
        if closed_tickets:
            for t in closed_tickets:
                del active_trades[t]
        with open(ACTIVE_TRADES_FILE, "w") as f:
            json.dump(active_trades, f, indent=4)
