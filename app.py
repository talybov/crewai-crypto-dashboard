import streamlit as st
import json
import os
import telebot
import threading

# --- КОНФИГУРАЦИЯ ---
FILES = {
    "agents": "bot_memory.json",
    "tasks": "tasks_log.json"
}

def init_data():
    if not os.path.exists(FILES["tasks"]):
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)
    if not os.path.exists(FILES["agents"]):
        data = {
            "agents": {
                "Аналитик": {"status": "💤 Спит", "role": "Анализ рынка"},
                "Менеджер": {"status": "💤 Спит", "role": "Координатор"}
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
        with open(FILES["tasks"], "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["tasks"].append({"task": task_text})
            f.seek(0); json.dump(data, f, ensure_ascii=False, indent=4); f.truncate()
        bot.reply_to(m, f"✅ Задача '{task_text}' добавлена!")

    @bot.message_handler(commands=['work'])
    def work_agent(m):
        target = m.text.replace("/work", "").strip()
        with open(FILES["tasks"], "r+", encoding="utf-8") as ft, \
             open(FILES["agents"], "r+", encoding="utf-8") as fa:
            
            tasks = json.load(ft)
            agents = json.load(fa)
            
            # ОТЛАДКА: Если бот пишет "нет задач", мы увидим, что реально лежит в файле
            if not tasks["tasks"]:
                bot.reply_to(m, f"❌ Нет задач! Содержимое файла: {tasks}")
                return
            
            found = False
            for name in agents["agents"]:
                if name.lower() == target.lower():
                    task = tasks["tasks"].pop(0)
                    agents["agents"][name]["status"] = "🚀 Работает"
                    found = True
                    bot.reply_to(m, f"✅ {name} взял: {task['task']}")
                    break
            
            if found:
                ft.seek(0); ft.truncate(); json.dump(tasks, ft, ensure_ascii=False, indent=4)
                fa.seek(0); fa.truncate(); json.dump(agents, fa, ensure_ascii=False, indent=4)
            else:
                bot.reply_to(m, "❌ Агент не найден!")

    bot.polling(none_stop=True)

if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")
col1, col2 = st.columns(2)
with open(FILES["agents"], "r", encoding="utf-8") as f: col1.json(json.load(f))
with open(FILES["tasks"], "r", encoding="utf-8") as f: col2.json(json.load(f))
time.sleep(1); st.rerun()
