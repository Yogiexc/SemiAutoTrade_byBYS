# 🤖 Hedge Fund Sniper Algo - Semi Auto Trade

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![MetaTrader 5](https://img.shields.io/badge/MetaTrader%205-Integrated-success.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Selamat datang di **Hedge Fund Sniper Algo**, sebuah sistem Algorithmic Trading mutakhir yang dibangun dengan Python untuk mengontrol MetaTrader 5 (MT5). Bot ini bukan sekadar *Expert Advisor* (EA) biasa, melainkan otak analitik sekelas institusi yang berjalan di latar belakang untuk memberikan analisis, rekomendasi, hingga eksekusi *auto-pilot* 24/7!

---

## 🌟 Fitur Utama (Kasta Tertinggi)

Sistem ini dibangun berdasarkan 4 Pilar Utama layaknya manajemen dana profesional (*Prop-Firm Ready*):

1. **⚔️ Pilar 1: Multi-Timeframe Momentum**
   - Menghitung Trend Jangka Panjang (H4) memakai EMA 50 & 200.
   - Mengkalibrasi area *Support & Resistance* (H1).
   - Menemukan momentum pemicu memakai RSI, MACD, dan pola *Candlestick* (M15 & M5).

2. **🛡️ Pilar 2: Risk Management (Anti Margin Call)**
   - **Daily Loss Protection**: Mengunci bot jika kerugian hari ini menyentuh batas (misal -3.0%).
   - **Max Open Position**: Mencegah *over-trading* (maksimal memegang 2 posisi bersamaan).
   - **Spread Filter**: Secara otomatis memblokir eksekusi saat spread melar (misal saat *news* atau pergantian sesi).

3. **👁️ Pilar 3: Smart Money Concepts (SMC)**
   - Mendeteksi jejak "Paus" dan Bank Sentral di dalam *chart*.
   - **BOS (Break of Structure)** & **CHOCH (Change of Character)**: Konfirmasi pembalikan atau penerusan tren secara fraktal.
   - **FVG (Fair Value Gap)**: Mendeteksi anomali harga dan likuiditas akibat HFT (*High-Frequency Trading*).

4. **💰 Pilar 4: Trade Management & Telegram Bot**
   - **Magic Number (777/888)**: Bot tidak akan mengganggu order manual milikmu.
   - **Auto Break-Even (Trailing Stop)**: Memindahkan Stop Loss ke harga Entry secara otomatis jika sudah *profit* (uangmu 100% aman).
   - **Telegram Reports**: Mengirimkan sinyal `WAIT`, `TARGET ACQUIRED`, `POSITION OPENED`, hingga 📊 **DAILY REPORT** (Win Rate & Profit Harian) langsung ke HP-mu!

5. **📊 Pilar 5: Institutional Grade Quant Data (NEW)**
   - **Performance Analyzer (Logger V2)**: Melacak otomatis setiap metrik *trading* (RSI, ADX, Spread, Trend H4) ke dalam `performance_history.csv` untuk keperluan evaluasi *Quant*.
   - **Tracking MAE & MFE**: Menganalisis *Floating Loss* terdalam (MAE) dan *Floating Profit* tertinggi (MFE) untuk menyempurnakan penempatan *Stop Loss* & *Take Profit*.
   - **Show-Off Mode (Saklar Pamer)**: Opsi rahasia untuk melonggarkan keamanan (*cooldown* 10 detik, abaikan *sideways*) khusus untuk keperluan demo/pamer ke teman, tanpa harus mengubah *code* inti.

---

## 🛠️ Cara Kerja & Arsitektur

Sistem ini memakai konsep **Scoring (0 - 100)**:
Algoritma tidak memakai aturan IF-THEN murahan. Ia mengumpulkan nilai dari SMC (Bobot 30%), Trend H4 (Bobot 20%), Momentum M15 (Bobot 20%), S/R H1 (Bobot 15%), dan Volatilitas M5 (Bobot 15%). 

Hanya jika skor mencapai batas **Sniper (85%)**, robot akan menarik pelatuknya!

### Bagaimana Python terhubung ke MT5?
Sangat mudah! Kami menggunakan library resmi `MetaTrader5` dari MetaQuotes.
Kode ajaibnya hanyalah:
```python
import MetaTrader5 as mt5

# Mengkoneksikan Python ke Terminal MT5 yang sedang terbuka di Windows
if not mt5.initialize():
    print("Gagal konek ke MT5!")
```
Setelah terkoneksi, Python bisa menyedot jutaan baris *historical data* dalam sepersekian detik menggunakan `mt5.copy_rates_from_pos()`.

---

## 🚀 Cara Instalasi & Penggunaan

1. **Clone Repository ini**
   ```bash
   git clone https://github.com/Yogiexc/SemiAutoTrade_byBYS.git
   cd SemiAutoTrade_byBYS
   ```

2. **Siapkan Virtual Environment & Dependencies**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install pandas numpy MetaTrader5 python-dotenv requests
   ```

3. **Siapkan Telegram Bot (Penting!)**
   - Buat bot lewat `@BotFather` di Telegram.
   - Buat file `.env` di dalam folder `mt5-connector` (dan `mt5-scalper`).
   - Isi file `.env` dengan format:
     ```env
     TELEGRAM_BOT_TOKEN=token_bot_kamu_di_sini
     TELEGRAM_CHAT_ID=chat_id_kamu_di_sini
     ```

4. **Pilih Mode Trading dan Jalankan Bot**
   - Pastikan aplikasi **MetaTrader 5 Windows** sedang terbuka dan sudah *Login*.
   - Nyalakan tombol **Algo Trading** (AutoTrading) di menu atas MT5.
   - Buka terminal, dan pilih mode mana yang ingin kamu jalankan:

   **Opsi A: SNIPER MODE (Aman, Santai, H4/M15)**
   ```bash
   cd mt5-connector
   python main.py
   ```

   **Opsi B: SCALPER MODE (Barbar, Cepat, HFT M1)**
   ```bash
   cd mt5-scalper
   ..\mt5-connector\venv\Scripts\python.exe main.py
   ```

---

## ⚠️ Disclaimer

Sistem ini awalnya dirancang sebagai asisten semi-otomatis untuk **Edukasi & Analisis Data**, yang kemudian dikembangkan menjadi *Full Auto-Pilot*. Kami **TIDAK BERTANGGUNG JAWAB** atas segala kerugian finansial yang terjadi akibat penggunaan *script* ini di akun *Real*. 

Selalu gunakan **Akun Demo (Paper Trading)** selama beberapa minggu untuk memahami karakteristik algoritma sebelum mempertaruhkan uang riil. *Trading* itu kejam, gunakan akal sehat, bukan emosi!

**Happy Trading & Salam Cuan! 📈**
*Built with logic, sweat, and lots of coffee by BYS.*
