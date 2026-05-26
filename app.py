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
    
    @bot.message_handler(commands=['work'])
    def work_agent(m):
        target_name = m.text.replace("/work", "").strip()
        agents_data = get_data("agents")
        tasks_data = get_data("tasks")
        
        # Поиск агента
        found_name = next((n for n in agents_data["agents"] if n.lower() == target_name.lower()), None)
        
        if found_name and tasks_data["tasks"]:
            # Забираем первую задачу
            task = tasks_data["tasks"].pop(0)
            agents_data["agents"][found_name]["status"] = "🚀 Работает"
            agents_data["agents"][found_name]["task"] = task["task"]
            
            # Сохраняем изменения
            with open(FILES["agents"], "w", encoding="utf-8") as f:
                json.dump(agents_data, f, ensure_ascii=False, indent=4)
            with open(FILES["tasks"], "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=4)
                
            bot.reply_to(m, f"✅ {found_name} взял задачу: {task['task']}")
        else:
            bot.reply_to(m, "❌ Либо такого агента нет, либо задач для выполнения не осталось!")

    @bot.message_handler(commands=['report'])
    def report_agent(m):
        # Команда /report Аналитик — выдаст имитацию отчета
        target_name = m.text.replace("/report", "").strip()
        data = get_data("agents")
        
        if target_name in data["agents"]:
            bot.reply_to(m, f"📊 Отчет от {target_name}:\nМонета BTC выросла на 2.5%, ETH на 1.8%. Рынок перегрет, рекомендую фиксацию.")
        else:
            bot.reply_to(m, "❌ Агент не найден.")

    bot.polling(none_stop=True)

if "TG_TOKEN" in st.secrets:
    threading.Thread(target=run_bot, daemon=True).start()

# --- ЦИКЛ ОБНОВЛЕНИЯ ---
while True:
    with placeholder.container():
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🤖 Агенты")
            st.json(get_data("agents"))
        with col2:
            st.subheader("📝 Лог задач")
            st.json(get_data("tasks"))
    time.sleep(1)
    st.rerun()
