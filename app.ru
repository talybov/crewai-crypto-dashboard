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

# --- ИНИЦИАЛИЗАЦИЯ ---
def init_data():
    if not os.path.exists(FILES["agents"]):
        data = {
            "agents": {
                "Исследователь": {"status": "Свободен", "history": ["Ожидание..."]},
                "Аналитик": {"status": "Свободен", "history": ["Ожидание..."]},
                "Риск-менеджер": {"status": "Свободен", "history": ["Ожидание..."]},
                "Разработчик": {"status": "Свободен", "history": ["Ожидание..."]},
                "Менеджер": {"status": "Свободен", "history": ["Ожидание..."]}
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- ИНСТРУМЕНТЫ АНАЛИЗА ---
def get_market_data(ticker):
    try:
        data = yf.Ticker(f"{ticker}-USD").info
        return f"Цена: ${data.get('currentPrice', 'N/A')}"
    except: return "Данные недоступны"

def get_news(ticker):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(f"{ticker} crypto news", max_results=1)]
            return results[0]['body'][:100] if results else "Нет свежих новостей"
    except: return "Ошибка поиска"

# --- ЛОГИКА АГЕНТОВ ---
def def get_agent_result(role, ticker, ticker_data, news_data):
    # Логика: Аналитик передает данные, а Риск-менеджер их фильтрует
    if role == "Исследователь":
        return f"Новости: {news_data[:100]}"
    
    if role == "Аналитик":
        return f"Рынок: {ticker_data}. Тренд: {'Рост' if 'цена' in ticker_data else 'Флэт'}"
    
    if role == "Риск-менеджер":
        # Если в новостях есть негатив, риск-менеджер блокирует сделку
        if "bad" in news_data.lower() or "crash" in news_data.lower():
            return "⚠️ РИСК: Высокий! Рекомендую выход из позиции."
        return "✅ РИСК: Приемлемый. Волатильность в норме."
    
    if role == "Разработчик":
        return "🔧 Скрипт: Мониторинг запущен, лимиты обновлены."
        
    if role == "Менеджер":
        # Логика принятия решения: Менеджер суммирует данные
        if "РИСК" in ticker_data: # Условная проверка
            return "❌ ВЕРДИКТ: Сделка ОТКЛОНЕНА из-за высокой волатильности."
        return "🚀 ВЕРДИКТ: Сделка ОДОБРЕНА. Вход по рынку."
    
    return "Ожидание..."

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(func=lambda m: True)
    def handle_message(m):
        ticker = m.text.upper()
        with open(FILES["agents"], "r+", encoding="utf-8") as fa:
            data = json.load(fa)
            roles = ["Исследователь", "Аналитик", "Риск-менеджер", "Разработчик", "Менеджер"]
            
            context = ticker
            for agent in roles:
                data["agents"][agent]["status"] = "В работе..."
                result = get_agent_result(agent, ticker, context)
                data["agents"][agent]["history"] = [f"🔹 {result}"]
                context = result
                data["agents"][agent]["status"] = "Свободен"
            
            fa.seek(0); fa.truncate(); json.dump(data, fa, ensure_ascii=False, indent=4)
        bot.reply_to(m, f"🚀 Анализ {ticker} выполнен!")

    bot.polling(none_stop=True)

if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")
with open(FILES["agents"], "r", encoding="utf-8") as f:
    data = json.load(f)

cols = st.columns(5)
for i, (name, info) in enumerate(data["agents"].items()):
    with cols[i]:
        st.subheader(name)
        if info["status"] == "Свободен": st.success("🟢 Свободен")
        else: st.warning("⚠️ В работе...")
        for event in info.get("history", []): st.caption(event)

time.sleep(2)
st.rerun()
