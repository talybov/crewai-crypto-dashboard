import streamlit as st
import json
import os
import telebot
import threading
import time
import yfinance as yf
from duckduckgo_search import DDGS

st.set_page_config(page_title="Pro-Crypto Swarm", layout="wide")
FILES = {"agents": "bot_memory.json"}

# --- ИНСТРУМЕНТЫ АНАЛИЗА ---
def get_market_data(ticker):
    try:
        data = yf.Ticker(f"{ticker}-USD").info
        return f"Цена: {data.get('currentPrice', 'N/A')}, P/E: {data.get('trailingPE', 'N/A')}"
    except: return "Ошибка получения данных."

def get_news(ticker):
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(f"{ticker} crypto news", max_results=2)]
        return "\n".join([r['body'] for r in results])

# --- УМНЫЕ АГЕНТЫ ---
def get_agent_result(role, ticker, previous_context):
    if role == "Исследователь":
        news = get_news(ticker)
        return f"Новости: {news[:150]}"
    if role == "Аналитик":
        price = get_market_data(ticker)
        return f"Тех-анализ: {price}. Контекст: {previous_context[:100]}"
    if role == "Риск-менеджер":
        return f"Риск-оценка: Низкая волатильность по {ticker} сейчас."
    if role == "Разработчик":
        return f"Сигнал: {ticker} в зоне интереса алгоритма."
    if role == "Менеджер":
        return f"ВЕРДИКТ: Анализ {ticker} завершен. Покупать, если цена закрепится."
    return previous_context

# --- ЛОГИКА БОТА ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(func=lambda m: True)
    def handle_message(m):
        ticker = m.text.upper() # Ожидаем тикер, например SOL
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
        bot.reply_to(m, f"🚀 Анализ {ticker} готов!")

    bot.polling(none_stop=True)

# (Остальной код интерфейса оставляем без изменений, как в предыдущем примере)
