import streamlit as st
import pandas as pd
import ta
import yfinance as yf
import telebot
import threading
import time
from datetime import datetime

# --- НАСТРОЙКИ ---
st.set_page_config(page_title="Autonomous Swarm", layout="wide")
TICKER = "BTC"

# --- ЛОГИКА АНАЛИЗА ---
def get_market_analysis(ticker):
    try:
        df = yf.download(f"{ticker}-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
        if df.empty: return None
        close_data = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
        
        rsi = ta.momentum.rsi(close_data, window=14).iloc[-1]
        price = close_data.iloc[-1]
        
        signal = "HOLD"
        if rsi < 30: signal = "BUY"
        elif rsi > 70: signal = "SELL"
        
        return {"price": float(price), "rsi": float(rsi), "signal": signal, "time": datetime.now().strftime("%H:%M")}
    except: return None

# --- ТЕЛЕГРАМ-БОТ ---
def run_bot():
    # Убедись, что TG_TOKEN в Secrets!
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(func=lambda m: True)
    def chat(m):
        if "как дела" in m.text.lower():
            bot.reply_to(m, "Рой в строю, дежурю на рынке. Всё под контролем!")
        else:
            data = get_market_analysis(TICKER)
            if data:
                bot.reply_to(m, f"BTC: ${data['price']:.2f} | RSI: {data['rsi']:.1f} | Сигнал: {data['signal']}")
            else:
                bot.reply_to(m, "Не могу достучаться до биржи, бро.")

    bot.polling(none_stop=True)

if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Автономный Рой")
data = get_market_analysis(TICKER)

if data:
    c1, c2, c3 = st.columns(3)
    c1.metric("Цена BTC", f"${data['price']:.2f}")
    c2.metric("RSI (14)", f"{data['rsi']:.2f}")
    c3.metric("Вердикт", data['signal'])
    
    if data['signal'] == "BUY": st.success("🚀 Ищем точку входа для покупки!")
    elif data['signal'] == "SELL": st.error("⚠️ Внимание: сигнал на продажу/выход!")
    else: st.info("Рынок спокоен, мониторинг продолжается.")
else:
    st.warning("Мониторинг активен... жду данные...")

time.sleep(60)
st.rerun()
