import streamlit as st
import json
import os
import telebot
import threading
import time
import yfinance as yf
from duckduckgo_search import DDGS

# --- НАСТРОЙКИ ---
st.set_page_config(page_title="Pro-Crypto Swarm", layout="wide")
FILES = {"agents": "bot_memory.json"}

# --- ФУНКЦИИ АНАЛИЗА ---
def get_market_data(ticker):
    try:
        data = yf.Ticker(f"{ticker}-USD").info
        return f"Цена: ${data.get('currentPrice', 'N/A')}"
    except: return "Данные недоступны"

def get_news(ticker):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(f"{ticker} crypto news", max_results=1)]
            return results[0]['body'][:100] if results else "Нет новостей"
    except: return "Ошибка поиска"

def get_agent_result(role, ticker, ticker_data, news_data):
    if role == "Исследователь": return f"Новости: {news_data}"
    if role == "Аналитик": return f"Рынок: {ticker_data}"
    if role == "Риск-менеджер": return "Риск: Низкий."
    if role == "Разработчик": return "Скрипт: Готов."
    if role == "Менеджер": return "Вердикт: Одобрено."
    return "..."

# --- ЛОГИКА БОТА ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(func=lambda m: True)
    def handle_message(m):
        ticker = m.text.upper()
        ticker_data = get_market_data(ticker)
        news_data = get_news(ticker)
        
        with open(FILES["agents"], "r+", encoding="utf-8") as fa:
            data = json.load(fa)
            roles = ["Исследователь", "Аналитик", "Риск-менеджер", "Разработчик", "Менеджер"]
            for agent in roles:
                data["agents"][agent]["status"] = "В работе..."
                res = get_agent_result(agent, ticker, ticker_data, news_data)
                data["agents"][agent]["history"] = [f"🔹 {res}"]
                data["agents"][agent]["status"] = "Свободен"
            fa.seek(0); fa.truncate(); json.dump(data, fa, ensure_ascii=False, indent=4)
        bot.reply_to(m, f"🚀 Анализ {ticker} завершен!")

    bot.polling(none_stop=True)

# Запуск бота в потоке
if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС (Читает только JSON) ---
st.title("🛰 Центр Управления Роем")
if os.path.exists(FILES["agents"]):
    with open(FILES["agents"], "r", encoding="utf-8") as f:
        data = json.load(f)
    cols = st.columns(5)
    for i, (name, info) in enumerate(data["agents"].items()):
        with cols[i]:
            st.subheader(name)
            st.write(info["status"])
            for event in info.get("history", []): st.caption(event)
time.sleep(2)
st.rerun()
