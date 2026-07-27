import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message: str):
    """
    Mengirim pesan ke Telegram menggunakan Bot API.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Telegram API Token atau Chat ID belum diset di .env")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("[+] Berhasil mengirim pesan ke Telegram")
            return True
        else:
            print(f"[-] Gagal mengirim pesan ke Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"[-] Error saat menghubungi Telegram API: {e}")
        return False

if __name__ == "__main__":
    send_telegram_message("🤖 Tes pesan dari Python Sniper Algo!")
