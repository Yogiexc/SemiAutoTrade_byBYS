# AI Trading Assistant (Bryan Edition)

Proyek ini bertujuan untuk membangun AI Trading Assistant yang mampu menganalisis market seperti seorang trader profesional menggunakan strategi Price Action, Multi Time Frame, Fibonacci, dan Smart Risk Management.

## Arsitektur

- **MT5 Connector** (Python): Menghubungkan ke terminal MetaTrader 5 untuk mengambil data harga. *Harus dijalankan di Windows.*
- **Backend** (FastAPI): API server untuk menjembatani komunikasi.
- **AI Engine**: Pemrosesan dan prompt engineering menggunakan LLM (OpenAI/Claude/Gemini).
- **Frontend** (Next.js): Dashboard sederhana untuk melihat status pair.
- **Database** (PostgreSQL): Jurnal trading.
- **Telegram Bot**: Mengirim notifikasi sinyal ke HP.

## Tahapan Saat Ini
Tahap inisialisasi: Membuat struktur folder dasar dan MT5 Connector awal.
