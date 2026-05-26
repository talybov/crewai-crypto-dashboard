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

def init_storage():
    if not os.path.exists(FILES["tasks"]):
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)
            
def setup_initial_agents():
    if not os.path.exists(FILES["agents"]):
        # Роли агентов как в видео: узкая специализация
        data = {
            "agents": {
                "Аналитик": {
                    "status": "💤 Спит", 
                    "task": "Нет", 
                    "role": "Анализ исторических данных и поиск паттернов",
                    "thought_process": ""
                },
                "Менеджер": {
                    "status": "💤 Спит", 
                    "task": "Нет", 
                    "role": "Управление очередью задач и координация",
                    "thought_process": ""
                }
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def get_data(key):
    with open(FILES[key], "r", encoding="utf-8") as f:
        return json.load(f)

init_storage()
setup_initial_agents()

# --- ЛОГИКА АГЕНТОВ ---
def agent_think(role, task):
    """Имитация цепочки размышлений агента"""
    if "Анализ" in role:
        return f"1. Сбор данных по задаче: {task}. 2. Проведение бэктеста. 3. Формирование торгового сигнала."
    return f"1. Оценка приоритета задачи: {task}. 2. Распределение ресурсов. 3. Контроль исполнения."

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(commands=['work'])
    def work_agent(m):
        target_name = m.text.replace("/work", "").strip()
        agents_data = get_data("agents")
        tasks_data = get_data("tasks")
        
        found_name = next((n for n in agents_data["agents"] if n.lower() == target_name.lower()), None)
        
        if found_name and tasks_data["tasks"]:
            task = tasks_data["tasks"].pop(0)
            role = agents_data["agents"][found_name]["role"]
            
            # Агент "думает" перед работой
            plan = agent_think(role, task["task"])
            
            agents_data["agents"][found_name].update({
                "status": "🚀 Работает",
                "task": task["task"],
                "thought_process": plan
            })
            
            with open(FILES["agents"], "w", encoding="utf-8") as f:
                json.dump(agents_data, f, ensure_ascii=False, indent=4)
            with open(FILES["tasks"], "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=4)
                
            bot.reply_to(m, f"🧠 {found_name} (Роль: {role})\nПлан действий:\n{plan}")
        else:
            bot.reply_to(m, "❌ Агент не найден или задач нет.")

    bot.polling(none_stop=True)

# Запуск бота (с защитой от дублей)
if "bot_started" not in st.session_state:
    if "TG_TOKEN" in st.secrets:
        threading.Thread(target=run_bot, daemon=True).start()
        st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.set_page_config(layout="wide")
st.title("🛰 Центр Управления Роем")
placeholder = st.empty()

while True:
    with placeholder.container():
        st.subheader("🤖 Активные агенты и их мысли")
        st.json(get_data("agents"))
        st.subheader("📝 Очередь задач")
        st.json(get_data("tasks"))
    time.sleep(1)
    st.rerun()
