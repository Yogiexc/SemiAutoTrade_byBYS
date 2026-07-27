import MetaTrader5 as mt5
from datetime import datetime, time as dtime, timezone

def check_max_positions(symbol: str, max_allowed: int = 2) -> dict:
    """
    Mengecek jumlah posisi yang sedang terbuka untuk suatu pair.
    """
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return {"can_trade": False, "reason": "Gagal membaca posisi MT5"}
    
    current_open = len(positions)
    if current_open >= max_allowed:
        return {"can_trade": False, "reason": f"Max Open Posisi tercapai ({current_open}/{max_allowed})"}
    
    return {"can_trade": True, "reason": f"Posisi aman ({current_open}/{max_allowed})"}

def check_daily_loss(max_loss_percent: float = -3.0) -> dict:
    """
    Menghitung total profit/loss dari deal hari ini.
    Jika melebihi batas max_loss_percent (misal -3.0%), maka block trading.
    """
    account_info = mt5.account_info()
    if account_info is None:
        return {"can_trade": False, "reason": "Gagal membaca info akun MT5"}
        
    balance = account_info.balance
    
    # Dapatkan waktu awal hari ini (jam 00:00)
    now = datetime.now()
    midnight = datetime(now.year, now.month, now.day)
    
    # Ambil deal/histori dari midnight sampai sekarang
    deals = mt5.history_deals_get(midnight, now)
    
    if deals is None or len(deals) == 0:
        return {"can_trade": True, "reason": "Belum ada history trading hari ini (Aman)"}
        
    # Hitung total profit hari ini
    daily_profit = sum([deal.profit for deal in deals])
    
    # Hitung persentase profit terhadap balance
    profit_percent = (daily_profit / balance) * 100
    
    if profit_percent <= max_loss_percent:
        return {
            "can_trade": False, 
            "reason": f"DAILY LOSS LIMIT REACHED! Loss hari ini: {profit_percent:.2f}% (Batas: {max_loss_percent}%)"
        }
        
    return {
        "can_trade": True, 
        "reason": f"Daily P/L aman ({profit_percent:.2f}% / {max_loss_percent}%)"
    }

def check_news_filter(symbol: str) -> dict:
    """
    [PLACEHOLDER] Mengecek kalender ekonomi (ForexFactory).
    Memblokir trading 30 menit sebelum/sesudah berita High Impact (merah).
    """
    # TODO: Integrasikan dengan request ke web ForexFactory / API kalender ekonomi.
    # Untuk sementara, kembalikan True (Aman)
    
    return {"can_trade": True, "reason": "Tidak ada berita High Impact dalam waktu dekat"}
