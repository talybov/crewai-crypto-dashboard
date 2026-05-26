import streamlit as st
import json
import os
import telebot
import time
import datetime
import threading
import random

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
    # Создаем структуру, если файла нет
    data = {
        "agents": {
            "Аналитик": {
                "status": "💤 Спит", "task": "Нет", 
                "role": "Анализ рынка", "thought_process": "Ожидание"
            },
            "Менеджер": {
                "status": "💤 Спит", "task": "Нет", 
                "role": "Координатор", "thought_process": "Ожидание"
            }
        }
    }
    # Принудительно перезаписываем, если файл старый/битый
    with open(FILES["agents"], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_data(key):
    with open(FILES[key], "r", encoding="utf-8") as f:
        return json.load(f)

# Инициализация
init_storage()
if not os.path.exists(FILES["agents"]):
    setup_initial_agents()

# --- ЛОГИКА ---
def agent_think(role, task):
    if role == "Анализ рынка":
        price = random.randint(60000, 70000)
        return f"1. Сбор данных (BTC: ${price}).\n2. Расчет индикаторов.\n3. Прогноз: {random.choice(['🟢 Рост', '🔴 Падение'])}."
    return f"1. Оценка задачи: {task}.\n2. Распределение ресурсов.\n3. Мониторинг выполнения."

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(commands=['work'])
    def work_agent(m):
        cmd = m.text.split()
        if len(cmd) < 2: 
            bot.reply_to(m, "Укажи имя: /work [Имя]")
            return
        
        target_name = cmd[1].strip()
        agents_data = get_data("agents")
        tasks_data = get_data("tasks")
        
        found_name = next((n for n in agents_data["agents"] if n.lower() == target_name.lower()), None)
        
        if found_name and tasks_data["tasks"]:
            task_obj = tasks_data["tasks"].pop(0)
            plan = agent_think(agents_data["agents"][found_name]["role"], task_obj["task"])
            
            agents_data["agents"][found_name].update({
                "status": "🚀 Работает",
                "task": task_obj["task"],
                "thought_process": plan
            })
            
            with open(FILES["agents"], "w", encoding="utf-8") as f:
                json.dump(agents_data, f, ensure_ascii=False, indent=4)
            with open(FILES["tasks"], "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=4)
                
            bot.reply_to(m, f"✅ {found_name} принял задачу: {task_obj['task']}\n\n🧠 ПЛАН:\n{plan}")
        else:
            bot.reply_to(m, "❌ Ошибка: нет задач или агент не найден.")

    bot.polling(none_stop=True)

# Запуск бота с защитой от дублей
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
        st.subheader("🤖 Агенты")
        st.json(get_data("agents"))
        st.subheader("📝 Очередь")
        st.json(get_data("tasks"))
    time.sleep(2)
    st.rerun()
