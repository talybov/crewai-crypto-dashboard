import streamlit as st
import json
import os
import telebot
import threading
import random
import time

FILES = {"agents": "bot_memory.json", "tasks": "tasks_log.json"}

# --- ИНИЦИАЛИЗАЦИЯ С ОБЩЕЙ ПАМЯТЬЮ ---
def init_data():
    if not os.path.exists(FILES["tasks"]):
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)
    if not os.path.exists(FILES["agents"]):
        data = {
            "agents": {
                "Аналитик": {"status": "💤 Спит", "role": "Аналитик", "history": []},
                "Менеджер": {"status": "💤 Спит", "role": "Координатор", "history": []},
                "Риск-менеджер": {"status": "💤 Спит", "role": "Риск", "history": []}
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- ЛОГИКА «ОБЩЕНИЯ» И «РАЗВИТИЯ» ---
def agent_communicate(sender, receiver, task_context):
    """Агент передает эстафету другому"""
    return f"[{sender} -> {receiver}]: Задача '{task_context}' обработана. Требуется проверка рисков."

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

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
            
            task = tasks["tasks"].pop(0)
            name = next((n for n in agents["agents"] if n.lower() == target.lower()), None)
            
            if name:
                # Агент работает и «пишет» в историю для коллеги
                reflection = f"Анализ завершен, передаю в отдел рисков."
                agents["agents"][name]["history"].append(f"Выполнил: {task['task']}. Итог: {reflection}")
                
                # Автоматическая передача «эстафеты»
                next_agent = "Риск-менеджер" if name != "Риск-менеджер" else "Менеджер"
                communication = agent_communicate(name, next_agent, task['task'])
                
                bot.reply_to(m, f"✅ {name} поработал.\n🧠 Мысли: {reflection}\n📢 {communication}")
                
                # Сохранение
                ft.seek(0); ft.truncate(); json.dump(tasks, ft, ensure_ascii=False, indent=4)
                fa.seek(0); fa.truncate(); json.dump(agents, fa, ensure_ascii=False, indent=4)
            else:
                bot.reply_to(m, "❌ Агент не найден!")

    bot.polling(none_stop=True)

# ... (запуск и интерфейс как в прошлый раз)
if "bot_started" not in st.session_state:
    if "TG_TOKEN" in st.secrets:
        threading.Thread(target=run_bot, daemon=True).start()
        st.session_state.bot_started = True

st.title("🛰 Центр Управления Роем")
with open(FILES["agents"], "r", encoding="utf-8") as f: st.json(json.load(f))
time.sleep(1); st.rerun()
