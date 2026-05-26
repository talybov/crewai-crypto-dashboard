import streamlit as st
import json
import os
import telebot
import time
import threading
import random

# --- КОНФИГУРАЦИЯ ---
FILES = {
    "agents": "bot_memory.json",
    "tasks": "tasks_log.json"
}

# --- ИНИЦИАЛИЗАЦИЯ ---
def init_data():
    # Принудительно удаляем старые файлы, чтобы создать новые
    for f_name in [FILES["tasks"], FILES["agents"]]:
        if os.path.exists(f_name):
            os.remove(f_name)
    
    # Теперь создаем свежие
    with open(FILES["tasks"], "w", encoding="utf-8") as f:
        json.dump({"tasks": []}, f)
    
    data = {
        "agents": {
            "Аналитик": {"status": "💤 Спит", "task": "Нет", "role": "Анализ рынка", "thought_process": "Ожидание"},
            "Менеджер": {"status": "💤 Спит", "task": "Нет", "role": "Координатор", "thought_process": "Ожидание"}
        }
    }
    with open(FILES["agents"], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    if not os.path.exists(FILES["agents"]):
        data = {
            "agents": {
                "Аналитик": {"status": "💤 Спит", "task": "Нет", "role": "Анализ рынка", "thought_process": "Ожидание"},
                "Менеджер": {"status": "💤 Спит", "task": "Нет", "role": "Координатор", "thought_process": "Ожидание"}
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(commands=['add'])
    def add_task(m):
        task_text = m.text.replace("/add", "").strip()
        if not task_text: return
        with open(FILES["tasks"], "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["tasks"].append({"task": task_text})
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=4)
        bot.reply_to(m, "✅ Задача в очереди!")

    @bot.message_handler(commands=['work'])
    def work_agent(m):
        target = m.text.replace("/work", "").strip()
        with open(FILES["tasks"], "r+", encoding="utf-8") as ft, \
             open(FILES["agents"], "r+", encoding="utf-8") as fa:
            
            tasks = json.load(ft)
            agents = json.load(fa)
            
            if not tasks["tasks"]:
                bot.reply_to(m, "❌ Нет задач!")
                return
            
            found = False
            for name in agents["agents"]:
                if name.lower() == target.lower():
                    task = tasks["tasks"].pop(0)
                    agents["agents"][name]["status"] = "🚀 Работает"
                    agents["agents"][name]["task"] = task["task"]
                    agents["agents"][name]["thought_process"] = f"План: 1. Анализ {task['task']}. 2. Прогноз рынка. 3. Отчет."
                    found = True
                    bot.reply_to(m, f"✅ {name} взял задачу: {task['task']}\n\n🧠 План:\n{agents['agents'][name]['thought_process']}")
                    break
            
            if found:
                ft.seek(0); ft.truncate(); json.dump(tasks, ft, ensure_ascii=False, indent=4)
                fa.seek(0); fa.truncate(); json.dump(agents, fa, ensure_ascii=False, indent=4)
            else:
                bot.reply_to(m, "❌ Агент не найден!")

    bot.polling(none_stop=True)

# Запуск
if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")
with open(FILES["agents"], "r", encoding="utf-8") as f: st.json(json.load(f))
with open(FILES["tasks"], "r", encoding="utf-8") as f: st.json(json.load(f))
time.sleep(1); st.rerun()
