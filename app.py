import streamlit as st
import pandas as pd
import ta
import yfinance as yf
import telebot
import threading
import time
from datetime import datetime

# --- КОНФИГ ---
st.set_config = st.set_page_config(page_title="Autonomous Swarm", layout="wide")
TICKERS = ["BTC", "ETH", "SOL", "ADA", "XRP"]

# --- ЛОГИКА АНАЛИЗА ---
@st.cache_data(ttl=60)
def get_analysis(ticker):
    try:
        df = yf.download(f"{ticker}-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
        if df.empty: return None
        close_data = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
        rsi = ta.momentum.rsi(close_data, window=14).iloc[-1]
        price = close_data.iloc[-1]
        signal = "BUY" if rsi < 30 else ("SELL" if rsi > 70 else "HOLD")
        return {"ticker": ticker, "price": float(price), "rsi": float(rsi), "signal": signal}
    except: return None

# --- ТЕЛЕГРАМ-БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    @bot.message_handler(func=lambda m: True)
    def chat(m):
        if "как дела" in m.text.lower():
            bot.reply_to(m, "Рой активен, мониторю рынок. Жду профитных сигналов!")
        else:
            bot.reply_to(m, "Мониторинг идет. Список активов: " + ", ".join(TICKERS))
    bot.polling(none_stop=True)

if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС (ЗАФИКСИРОВАННЫЙ СКЕЛЕТ) ---
st.title("🛰 Автономный Рой: Мульти-валютный мониторинг")

# Создаем контейнеры, чтобы они не пропадали
main_placeholder = st.empty()
log_placeholder = st.empty()

while True:
    results = [get_analysis(t) for t in TICKERS]
    results = [r for r in results if r]
    
    with main_placeholder.container():
        st.subheader("📊 Статистика активов")
        df = pd.DataFrame(results)
        st.table(df)
        
        # Подсветка целей
        buys = df[df['signal'] == 'BUY']
        if not buys.empty:
            st.success(f"🚀 Покупать: {', '.join(buys['ticker'].tolist())}")
            
    with log_placeholder.container():
        st.subheader("📋 Логи работы роя")
        st.caption(f"Последнее обновление: {datetime.now().strftime('%H:%M:%S')}")
        for res in results:
            if res['signal'] != "HOLD":
                st.write(f"Агент Аналитик: {res['ticker']} имеет RSI {res['rsi']:.1f} — статус {res['signal']}")

    time.sleep(60)
    st.rerun()
