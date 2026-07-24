def format_bot_online(strategy="Hedge Fund Sniper v2", broker="MetaQuotes Demo"):
    return (
        f"🤖 <b>SNIPER BOT ONLINE</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Status    : ACTIVE\n"
        f"Mode      : AUTO PILOT\n"
        f"Strategy  : {strategy}\n"
        f"Broker    : {broker}\n"
        f"Server    : Connected\n\n"
        f"📡 Monitoring market 24/7...\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

def format_monitoring_wait(symbol, score, buy_score, sell_score, reasons):
    reason_str = "\n".join([f"• {r}" for r in reasons])
    return (
        f"⌛ <b>MARKET STATUS : WAIT</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Pair      : {symbol}\n"
        f"Score     : {score}%\n\n"
        f"BUY  : {buy_score}%\n"
        f"SELL : {sell_score}%\n\n"
        f"Status :\n"
        f"❌ Belum memenuhi syarat entry\n\n"
        f"Alasan:\n"
        f"{reason_str}\n\n"
        f"Robot tetap memantau...\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

def format_target_acquired(symbol, direction, score, session, spread):
    return (
        f"🎯 <b>TARGET ACQUIRED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Pair : {symbol}\n"
        f"Side : {direction}\n\n"
        f"Confidence : {score}%\n\n"
        f"Session : {session}\n\n"
        f"Spread : {spread:.1f} pip\n\n"
        f"Semua filter lolos.\n\n"
        f"Menunggu eksekusi...\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

def format_position_opened(symbol, direction, lot, entry, sl, tp, score, reasons, ticket):
    reason_str = "\n".join([f"✅ {r}" for r in reasons])
    
    return (
        f"🟢 <b>POSITION OPENED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Pair     : {symbol}\n"
        f"Action   : {direction}\n\n"
        f"Lot      : {lot}\n\n"
        f"Entry    : {entry:.5f}\n\n"
        f"StopLoss : {sl:.5f}\n\n"
        f"TakeProfit : {tp:.5f}\n\n"
        f"Risk Reward : 1 : 3\n\n"
        f"Confidence : {score}%\n\n"
        f"Reason :\n"
        f"{reason_str}\n\n"
        f"Ticket :\n"
        f"{ticket}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

def format_risk_protection(loss_percent):
    return (
        f"🛑 <b>RISK PROTECTION</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Trading dihentikan.\n\n"
        f"Daily Loss :\n"
        f"{loss_percent}%\n\n"
        f"Batas harian tercapai.\n\n"
        f"Robot akan aktif kembali\n"
        f"besok pukul 00:00.\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

def format_news_filter(currency, news_title, minutes):
    return (
        f"🚨 <b>HIGH IMPACT NEWS</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{currency}\n\n"
        f"{news_title}\n\n"
        f"Dalam\n"
        f"{minutes} Menit\n\n"
        f"Trading dihentikan sementara.\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

def format_spread_filter(symbol, current_spread, max_spread):
    return (
        f"⚠️ <b>MARKET FILTER</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Spread terlalu tinggi.\n\n"
        f"{symbol}\n\n"
        f"Current :\n"
        f"{current_spread:.1f} pip\n\n"
        f"Maximum :\n"
        f"{max_spread:.1f} pip\n\n"
        f"Robot WAIT.\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
