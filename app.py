import streamlit as st
import json, os, threading, telebot

# --- 1. КОНФИГУРАЦИЯ ---
FILES = {
    "agents": "bot_memory.json",
    "tasks": "tasks_log.json"
}

# --- 2. ЯДРО СИСТЕМЫ (Работа с памятью) ---
def init_storage():
    """Создает файлы, если их нет."""
    if not os.path.exists(FILES["agents"]):
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump({"agents": {}}, f)
    if not os.path.exists(FILES["tasks"]):
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)

def get_data(key):
    with open(FILES[key], "r", encoding="utf-8") as f:
        return json.load(f)

# --- 3. ИНТЕРФЕЙС (Сайт) ---
st.set_page_config(page_title="Swarm Control", layout="wide")
init_storage()

st.title("🛰 Центр Управления Роем")

# Блок мониторинга
col1, col2 = st.columns(2)
with col1:
    st.subheader("Агенты")
    st.json(get_data("agents"))
with col2:
    st.subheader("Лог задач")
    st.json(get_data("tasks"))

# --- 4. БОТ (Telegram) ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(commands=['start'])
    def start(m):
        bot.reply_to(m, "Рой готов. Используй /work [имя] для запуска.")
        
    bot.polling(none_stop=True)

if "TG_TOKEN" in st.secrets:
    threading.Thread(target=run_bot, daemon=True).start()
