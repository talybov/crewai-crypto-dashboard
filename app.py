import streamlit as st
import json
import os
import telebot
import time
import datetime
import threading

# --- КОНФИГУРАЦИЯ ---
FILES = {
    "agents": os.path.join(os.getcwd(), "bot_memory.json"),
    "tasks": os.path.join(os.getcwd(), "tasks_log.json")
}

# --- ЯДРО СИСТЕМЫ ---
def init_storage():
    if not os.path.exists(FILES["tasks"]):
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)
            
def setup_initial_agents():
    if not os.path.exists(FILES["agents"]):
        data = {
            "agents": {
                "Аналитик": {"status": "💤 Спит", "task": "Ожидание"},
                "Менеджер": {"status": "💤 Спит", "task": "Ожидание"}
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def get_data(key):
    with open(FILES[key], "r", encoding="utf-8") as f:
        return json.load(f)

init_storage()
setup_initial_agents()

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Swarm Control", layout="wide")
st.title("🛰 Центр Управления Роем")
placeholder = st.empty()

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(commands=['start'])
    def start(m):
        bot.reply_to(m, "Рой на связи. /add [задача] — добавить, /work [агент] — разбудить.")

    @bot.message_handler(commands=['add'])
    def add_task(m):
        task_text = m.text.replace("/add", "").strip()
        data = get_data("tasks")
        data["tasks"].append({"task": task_text, "status": "Ожидает"})
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        bot.reply_to(m, "✅ Задача добавлена!")

    @bot.message_handler(commands=['work'])
    def work_agent(m):
        cmd_parts = m.text.split()
        if len(cmd_parts) < 2:
            bot.reply_to(m, "Укажи имя агента: /work Аналитик")
            return
        
        target_name = cmd_parts[1].strip()
        data = get_data("agents")
        
        # Поиск с учетом регистра
        found_name = None
        for name in data["agents"].keys():
            if name.lower() == target_name.lower():
                found_name = name
                break
        
        if found_name:
            data["agents"][found_name]["status"] = "🚀 Работает"
            with open(FILES["agents"], "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            bot.reply_to(m, f"✅ {found_name} проснулся!")
        else:
            bot.reply_to(m, f"❌ Агент '{target_name}' не найден. Доступные: {', '.join(data['agents'].keys())}")

    bot.polling(none_stop=True)

# Запуск бота
if "TG_TOKEN" in st.secrets:
    threading.Thread(target=run_bot, daemon=True).start()

# --- ЦИКЛ ОБНОВЛЕНИЯ ---
while True:
    with placeholder.container():
        st.write(f"⏰ Обновлено: {datetime.datetime.now().strftime('%H:%M:%S')}")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🤖 Агенты")
            st.json(get_data("agents"))
        with col2:
            st.subheader("📝 Лог задач")
            st.json(get_data("tasks"))
    
    time.sleep(1)
    st.rerun()
