import streamlit as st
import pandas as pd
import ta
import yfinance as yf
import telebot
import threading
import time
from datetime import datetime

# --- КОНФИГ ---
st.set_page_config(page_title="Autonomous Swarm", layout="wide")
TICKER = "BTC"

# --- ФУНКЦИЯ ДАННЫХ ---
@st.cache_data(ttl=60) # Кэшируем данные на 60 секунд, чтобы сайт не "мигал"
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
        return {"price": float(price), "rsi": float(rsi), "signal": signal}
    except: return None

# --- ИНТЕРФЕЙС (Каркас) ---
st.title("🛰 Автономный Рой: Аналитика")

# 1. МЕТРИКИ (Они всегда на месте)
placeholder = st.empty() 

# 2. АВТОНОМНЫЙ ЦИКЛ
while True:
    data = get_market_analysis(TICKER)
    
    with placeholder.container():
        if data:
            c1, c2, c3 = st.columns(3)
            c1.metric("Цена BTC", f"${data['price']:.2f}")
            c2.metric("RSI (14)", f"{data['rsi']:.2f}")
            c3.metric("Вердикт", data['signal'])
            
            if data['signal'] == "BUY": st.success("🚀 Ищем точку входа!")
            elif data['signal'] == "SELL": st.error("⚠️ Сигнал на продажу!")
            else: st.info("Рынок нейтрален, мониторинг...")
        else:
            st.warning("⚠️ Ожидание данных от биржи...")
            
    time.sleep(60) # Ждем минуту
