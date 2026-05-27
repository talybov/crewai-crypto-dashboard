import streamlit as st
import pandas as pd
import ta
import yfinance as yf
import telebot
import json
import time
from datetime import datetime

# --- КОНФИГ ---
st.set_page_config(page_title="Autonomous Swarm", layout="wide")
TICKER = "BTC"

def get_market_analysis(ticker):
    # Добавляем auto_adjust=True, чтобы очистить данные от лишних уровней
    df = yf.download(f"{ticker}-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
    
    if df.empty: return None
    
    # Принудительно выбираем колонку 'Close' и превращаем её в Series
    # Если df['Close'] - это DataFrame (из-за мультииндекса), берем первую колонку
    close_data = df['Close']
    if isinstance(close_data, pd.DataFrame):
        close_data = close_data.iloc[:, 0]
        
    # Теперь точно передаем 1D Series
    rsi = ta.momentum.rsi(close_data, window=14).iloc[-1]
    price = close_data.iloc[-1]
    
    signal = "HOLD"
    if rsi < 30: signal = "BUY"
    elif rsi > 70: signal = "SELL"
    
    return {"price": float(price), "rsi": float(rsi), "signal": signal, "time": datetime.now().strftime("%H:%M")}
# --- ТЕЛЕГРАМ-БОТ (ДРУГ) ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(m):
        bot.reply_to(m, "Привет, бро! Я твой рой. Слежу за рынком 24/7. Спроси меня 'Как дела?'")

    @bot.message_handler(func=lambda m: True)
    def chat(m):
        if "как дела" in m.text.lower():
            bot.reply_to(m, "Рынок дергается, я на чеку. Депозит в безопасности, жду хорошую точку входа!")
        else:
            data = get_market_analysis(TICKER)
            bot.reply_to(m, f"Ситуация по {TICKER}: Цена ${data['price']:.2f}, RSI: {data['rsi']:.1f}. Сигнал: {data['signal']}")

    bot.polling(none_stop=True)

# --- ЗАПУСК ---
if "bot_started" not in st.session_state:
    import threading
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Автономный Рой: Аналитика в реальном времени")
data = get_market_analysis(TICKER)

if data:
    col1, col2, col3 = st.columns(3)
    col1.metric("Цена BTC", f"${data['price']:.2f}")
    col2.metric("RSI (14)", f"{data['rsi']:.2f}")
    col3.metric("Рекомендация", data['signal'])

    if data['signal'] == "BUY": st.success("Сигнал на ПОКУПКУ!")
    elif data['signal'] == "SELL": st.error("Сигнал на ПРОДАЖУ!")
    else: st.info("Рынок нейтрален. Ждем.")
else:
    st.warning("Данные с рынка пока не поступили. Повторная попытка через 60 сек...")

time.sleep(60)
st.rerun()

col1, col2, col3 = st.columns(3)
col1.metric("Цена BTC", f"${data['price']:.2f}")
col2.metric("RSI (14)", f"{data['rsi']:.2f}")
col3.metric("Рекомендация", data['signal'])

if data['signal'] == "BUY": st.success("Сигнал на ПОКУПКУ!")
elif data['signal'] == "SELL": st.error("Сигнал на ПРОДАЖУ!")
else: st.info("Рынок нейтрален. Ждем.")

time.sleep(60)
st.rerun()
