import urllib.request
import json

TOKEN = "8662922663:AAH5ayM9hEFTVGsCqR6ML-gUy34DVXFZLXE"
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
