import streamlit as st
import json
import os
import telebot
import threading
import random

# --- КОНФИГУРАЦИЯ ---
FILES = {
    "agents": "bot_memory.json",
    "tasks": "tasks_log.json"
}

# --- ИНИЦИАЛИЗАЦИЯ РОЯ ---
def init_data():
    if not os.path.exists(FILES["tasks"]):
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)
    
    if not os.path.exists(FILES["agents"]):
        # Расширяем состав роя до 5 специалистов
        data = {
            "agents": {
                "Аналитик": {"status": "💤 Спит", "role": "Анализ рынка и поиск паттернов"},
                "Менеджер": {"status": "💤 Спит", "role": "Координатор очереди задач"},
                "Исследователь": {"status": "💤 Спит", "role": "Мониторинг Twitter и новостей"},
                "Риск-менеджер": {"status": "💤 Спит", "role": "Анализ рисков и стоп-лоссов"},
                "Разработчик": {"status": "💤 Спит", "role": "Исполнение кода и автоматизация"}
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- ЛОГИКА РАССУЖДЕНИЙ ---
def agent_think(role, task):
    responses = {
        "Анализ рынка": "1. Выгрузка исторических данных. 2. Технический анализ. 3. Формирование прогноза.",
        "Координатор": "1. Оценка приоритета. 2. Распределение нагрузки. 3. Мониторинг исполнения.",
        "Мониторинг Twitter и новостей": "1. Скрапинг ленты. 2. Анализ тональности новостей. 3. Отчет по хайпу.",
        "Анализ рисков и стоп-лоссов": "1. Оценка волатильности. 2. Расчет уровней ликвидации. 3. Настройка стопов.",
        "Исполнение кода и автоматизация": "1. Подготовка скриптов. 2. Прогон через песочницу. 3. Деплой на сервер."
    }
    return responses.get(role, "1. Изучение задачи. 2. Выполнение. 3. Отчет.")

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
            f.seek(0); f.truncate(); json.dump(data, f, ensure_ascii=False, indent=4)
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
                    plan = agent_think(agents["agents"][name]["role"], task["task"])
                    
                    agents["agents"][name].update({"status": "🚀 Работает", "task": task["task"], "thought_process": plan})
                    found = True
                    bot.reply_to(m, f"✅ {name} (Роль: {agents['agents'][name]['role']})\n\n🧠 ПЛАН:\n{plan}")
                    break
            
            if found:
                ft.seek(0); ft.truncate(); json.dump(tasks, ft, ensure_ascii=False, indent=4)
                fa.seek(0); fa.truncate(); json.dump(agents, fa, ensure_ascii=False, indent=4)
            else:
                bot.reply_to(m, "❌ Агент не найден!")

    bot.polling(none_stop=True)

if "bot_started" not in st.session_state:
    if "TG_TOKEN" in st.secrets:
        threading.Thread(target=run_bot, daemon=True).start()
        st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")
col1, col2 = st.columns(2)
with open(FILES["agents"], "r", encoding="utf-8") as f: col1.subheader("🤖 Агенты"); col1.json(json.load(f))
with open(FILES["tasks"], "r", encoding="utf-8") as f: col2.subheader("📝 Очередь"); col2.json(json.load(f))

import time
time.sleep(1); st.rerun()
