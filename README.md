# SemiAutoTrade by BYS

![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![MetaTrader 5](https://img.shields.io/badge/MetaTrader%205-integrated-success.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-demo%20testing-orange.svg)

A semi-automatic algorithmic trading system written in Python that controls MetaTrader 5 (MT5). It combines multi-timeframe signal scoring, strict risk management, Telegram notifications, and a quant-style trade logging pipeline for data-driven strategy optimization.

> Educational project. Use demo accounts only until results are statistically validated. Not financial advice.

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Trading Modes](#trading-modes)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Trade Logging and Analysis](#trade-logging-and-analysis)
- [Experiment Log](#experiment-log)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

## Features

**Signal engine**
- Multi-timeframe analysis: H4 / H1 trend, M15 / M5 momentum, M1 entries.
- Indicators: EMA, RSI, ADX, ATR, Bollinger Bands, MACD, candlestick patterns.
- Smart Money Concepts: Break of Structure (BOS), Change of Character (CHOCH), Fair Value Gap (FVG).
- Confidence scoring (0 to 100) instead of simple if/else rules.

**Risk management**
- Daily loss protection.
- Maximum open positions and layered entries with graded lot sizes.
- Spread, ADX (sideways), RSI (overbought / oversold) and reversal-candle filters.
- ATR-based stop loss and take profit, break-even and trailing stop.
- Magic number isolation, so manual orders are never touched.

**Operations**
- Telegram alerts for start, entry, trailing, close and daily report.
- Closed-trade detection that also recovers trades closed while the bot was offline.

**Data pipeline (Logger V4)**
- Unique `Trade_ID`, `Strategy_Version` and `Market_Regime` per trade.
- Balance and equity snapshot at entry.
- MAE / MFE tracking, holding time, and exit reason (SL, TP, trailing, auto-close, manual).
- Versioned strategy parameters in `mt5-scalper/experiments/`.

## Architecture

```text
mt5-scalper/
  main.py               entry point, scoring and execution loop
  analyzer.py           indicators and pattern detection
  data_fetcher.py       multi-timeframe data from MT5
  executor.py           order execution
  trade_manager.py      trailing stop and auto-close
  risk_manager.py       daily loss, max positions, news filter
  performance_logger.py trade logging (CSV) with MAE / MFE
  telegram_bot.py       notifications
  experiments/          versioned strategy configs
mt5-connector/          sniper mode (H4 / M15, SMC based)
backend/                API service (Docker)
docs/                   additional documentation
```

Python connects to MT5 through the official `MetaTrader5` package:

```python
import MetaTrader5 as mt5

if not mt5.initialize():
    raise RuntimeError(f"MT5 connection failed: {mt5.last_error()}")
```

## Trading Modes

Set `TRADING_MODE` at the top of `mt5-scalper/main.py`.

| Mode | Style | Cooldown | Max layers | Notes |
|---|---|---|---|---|
| `SWING_SAFE` | Conservative | 5 min | 3 | Higher score threshold |
| `HFT_PRO` | High activity M1 scalper | 30 s | 5 | Graded lots, tight trailing |
| `TURBO_M1` | Fast demo session | 10 s | 3 | Relaxed filters, close TP, ATR stop |

Note: this is a high-activity momentum scalper on Python and MT5, not true high-frequency trading.

## Installation

Requirements: Windows, MetaTrader 5 terminal (logged in), Python 3.9+.

```bash
git clone https://github.com/Yogiexc/SemiAutoTrade_byBYS.git
cd SemiAutoTrade_byBYS
python -m venv venv
.\venv\Scripts\activate
pip install -r mt5-scalper/requirements.txt
```

## Configuration

Copy `.env.example` to `.env` inside `mt5-scalper` (and `mt5-connector` if used):

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Never commit `.env`. It is already listed in `.gitignore`. Create the bot with `@BotFather` and revoke the token immediately if it is ever exposed.

In MT5, enable **Algo Trading** (toolbar button, `Ctrl+E`). Otherwise orders are rejected with error code 10027.

## Running the Bot

Scalper:

```bash
cd mt5-scalper
python main.py
```

Sniper (swing style):

```bash
cd mt5-connector
python main.py
```

## Trade Logging and Analysis

Every closed trade is appended to `mt5-scalper/performance_history.csv` with these columns:

`Trade_ID, Date, Ticket, Symbol, Type, Session, Spread_Cat, Score, Trend_H4, Trend_H1, RSI, ADX, ATR, Candle, Strategy_Version, Market_Regime, Balance, Equity, Entry_Price, Exit_Price, MAE, MFE, Profit, Holding_Time_Seconds, Exit_Reason, Magic_Number`

Analyze by session, regime, score band and exit reason to find the bottleneck, change one parameter, then compare with the same number of trades.

## Experiment Log

| ID | Mode | Result (demo, 1 hour) | Finding |
|---|---|---|---|
| 001 | `TURBO_M1` | 102 trades, 58% win rate, net -42.47 | Average loss (-2.37) was more than twice the average win (+1.01). The hard USD auto-close accounted for most of the loss (36 trades, -78.57), while trades closed by normal SL, TP and trailing were net positive. |

Next experiment: remove the hard USD cut-loss, reduce XAUUSD lot size, trade only the London and New York sessions.

## Roadmap

1. Collect 500 clean demo trades with a frozen strategy (bug fixes only).
2. Analyze by session, regime and score, then optimize one parameter per experiment.
3. Add an emergency stop loss on every order.
4. Move to 24/7 hosting (Windows VPS) after the strategy is validated.

## Disclaimer

This software is provided for education and data analysis. The authors are not responsible for any financial loss caused by using it on a live account. Test on a demo account first and never risk money you cannot afford to lose.

Built by Bryan Yogie Saputra (BYS). Licensed under MIT.
