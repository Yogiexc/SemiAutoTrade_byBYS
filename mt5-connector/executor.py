import MetaTrader5 as mt5

def execute_trade(symbol: str, direction: str, sl_price: float, tp_price: float, lot: float = 0.01) -> bool:
    """
    Mengeksekusi order BUY atau SELL di MT5.
    """
    # Pastikan symbol terlihat di Market Watch
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"[-] Symbol {symbol} tidak ditemukan.")
        return False

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print(f"[-] Gagal memunculkan {symbol} di Market Watch.")
            return False

    # Dapatkan tick harga terakhir
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"[-] Gagal mendapatkan tick data untuk {symbol}.")
        return False
        
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "BUY" else tick.bid
    
    # Setup Order Request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 20,
        "magic": 777,
        "comment": "Sniper Algo Trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # Kirim order
    print(f"[*] Mengeksekusi order {direction} untuk {symbol}...")
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        err_msg = f"Error Code: {result.retcode}"
        print(f"[-] Eksekusi GAGAL! {err_msg}")
        if result.retcode == 10027:
            print("    Alasan: 'Algo Trading' di MT5 belum diaktifkan.")
        return False, err_msg
    else:
        print(f"[+] Eksekusi BERHASIL! (Tiket: {result.order})")
        print(f"    Harga Entry : {result.price}")
        return True, result.order
