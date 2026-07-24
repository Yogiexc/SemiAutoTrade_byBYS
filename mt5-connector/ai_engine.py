import os
from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Skema Output sesuai dengan format SOP Bryan
class TradingSignal(BaseModel):
    trend: str
    confidence: int
    reason: List[str]
    recommendation: str

def get_ai_analysis(symbol: str, h4_trend: str, h1_sup: float, h1_res: float, m15_pattern: str, current_price: float) -> TradingSignal:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("GEMINI_API_KEY belum di-set di file .env!")
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Anda adalah AI Trading Assistant profesional yang menganalisis market menggunakan strategi Price Action, Multi Time Frame, dan Smart Risk Management.
    
    Data Market Saat Ini untuk {symbol}:
    - Harga Terkini: {current_price}
    - Trend H4: {h4_trend}
    - Support H1: {h1_sup}
    - Resistance H1: {h1_res}
    - Pola Candlestick M15 Terakhir: {m15_pattern}
    
    SOP Trading:
    1. Jika Trend H4 BUY, maka hanya cari peluang BUY.
    2. Entry BUY terbaik adalah ketika harga mendekati Support H1, dan ada konfirmasi Bullish Engulfing/Hammer di M15/M5.
    3. Jika Trend H4 SELL, maka hanya cari peluang SELL.
    4. Entry SELL terbaik adalah ketika harga mendekati Resistance H1, dan ada konfirmasi Bearish Engulfing/Shooting Star di M15/M5.
    5. Jika syarat belum terpenuhi, rekomendasikan WAIT.
    
    Evaluasi data di atas dan tentukan apakah saat ini adalah momen yang tepat untuk BUY, SELL, atau WAIT.
    Berikan alasan singkat dalam bentuk list, dan sebutkan confidence score (0-100%).
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TradingSignal,
                temperature=0.2, # Low temperature for more logical/consistent answers
            ),
        )
        return response.parsed
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None
