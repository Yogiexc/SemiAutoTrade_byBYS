import MetaTrader5 as mt5
import time

def place_test_order(symbol="EURUSD", lot=0.01):
    if not mt5.initialize():
        print(f"MT5 initialization failed, error: {mt5.last_error()}")
        return

    print(f"MT5 Initialized! Attempting to open a TEST BUY position for {symbol}...")

    # Cek apakah symbol ada
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} tidak ditemukan.")
        mt5.shutdown()
        return

    # Pastikan symbol terlihat di Market Watch
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print(f"Gagal memunculkan {symbol} di Market Watch.")
            mt5.shutdown()
            return

    # Ambil harga ask terbaru
    point = symbol_info.point
    ask = mt5.symbol_info_tick(symbol).ask

    # Setup Order Request (BUY 0.01 Lot)
    # SL 15 Pips, TP 45 Pips (1:3 Risk Reward)
    sl_points = 150 * point # 15 pips
    tp_points = 450 * point # 45 pips
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": ask,
        "sl": ask - sl_points,
        "tp": ask + tp_points,
        "deviation": 20,
        "magic": 234000,
        "comment": "Test Python AI",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    # Kirim order
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"\nOrder GAGAL! Error Code: {result.retcode}")
        if result.retcode == 10027:
            print("Alasan: 'Algo Trading' di aplikasi MT5-mu belum diaktifkan (Tombol Algo Trading masih merah).")
    else:
        print(f"\nOrder BERHASIL dieksekusi!")
        print(f"Tiket Order : {result.order}")
        print(f"Harga Open  : {result.price}")
        print(f"Volume      : {result.volume}")

    mt5.shutdown()

if __name__ == "__main__":
    place_test_order()
