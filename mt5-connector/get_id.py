import urllib.request
import json

import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

try:
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    if len(data.get("result", [])) > 0:
        chat_id = data["result"][0]["message"]["chat"]["id"]
        print(f"CHAT_ID_FOUND: {chat_id}")
    else:
        print("NO_MESSAGES_YET")
except Exception as e:
    print(f"ERROR: {e}")
