import streamlit as st
import pandas as pd
import ta
import yfinance as yf
import telebot
import threading
import time
from datetime import datetime
import json
import os
import streamlit as st
from agent_state import get_all_states
def draw_office_layout():
    st.subheader("🏢 Операционный штаб ИИ-агентов")
    states = get_all_states()
    
    # Создаем сетку из колонок, имитирующую столы
    cols = st.columns(3)
    
    # Список ваших агентов (например, Агент-Аналитик, Агент-Трейдер, Ванечка)
    agents_list = ["Аналитик", "Трейдер", "Ванечка"]
    
    for i, name in enumerate(agents_list):
        with cols[i % 3]:
            # Получаем статус для конкретного агента
            info = states.get(name, {"status": "Спит", "task": "Ожидание"})
            
            # Визуализация "стола" агента
            st.markdown(f"""
            <div style="padding: 10px; border: 2px solid #4CAF50; border-radius: 10px; text-align: center;">
                <h4>{name}</h4>
                <p><b>Статус:</b> {info['status']}</p>
                <p><small>{info['task']}</small></p>
            </div>
            """, unsafe_allow_html=True)
# ... ваш существующий код для графиков и Bybit ...

def show_agent_office():
    st.sidebar.subheader("🏢 Офис ИИ-агентов")
    states = get_all_states()
    
    if not states:
        st.sidebar.info("Агенты еще не начали работу...")
    else:
        for agent, info in states.items():
            status_color = "🟢" if info['status'] == "Активен" else "⚪"
            st.sidebar.markdown(f"**{status_color} {agent}**")
            st.sidebar.caption(f"Задача: {info['task']}")
            st.sidebar.divider()

# Основная логика дашборда
def main():
    st.title("Crypto Trading AI Dashboard")
    
    # Вызываем наш новый блок
    show_agent_office()
    
    # ... ваш существующий функционал (графики, кнопки) остается здесь ...

if __name__ == "__main__":
    main()
STATE_FILE = "agent_states.json"

def update_agent_status(agent_name, status, task):
    # Загружаем текущие статусы
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}
    
    # Обновляем статус
    data[agent_name] = {"status": status, "task": task}
    
    # Сохраняем
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def get_all_states():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

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
