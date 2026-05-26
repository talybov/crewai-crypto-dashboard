import streamlit as st
import json
import os
import telebot
import threading
import time

FILES = {"agents": "bot_memory.json", "tasks": "tasks_log.json"}

# --- ИНИЦИАЛИЗАЦИЯ ---
def init_data():
    if not os.path.exists(FILES["tasks"]):
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)
    
    # Принудительно создаем структуру, если ее нет
    default_data = {
        "agents": {
            "Аналитик": {"history": ["Система запущена..."]},
            "Риск-менеджер": {"history": ["Ожидание данных..."]},
            "Менеджер": {"history": ["Координация активна..."]}
        }
    }
    
    if not os.path.exists(FILES["agents"]):
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)

init_data()

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(commands=['work'])
    def work_agent(m):
        target = m.text.replace("/work", "").strip()
        with open(FILES["agents"], "r+", encoding="utf-8") as fa:
            data = json.load(fa)
            
            if target in data["agents"]:
                msg = f"🧠 Начал анализ задачи: {time.strftime('%H:%M:%S')}"
                data["agents"][target].setdefault("history", []).append(msg)
                
                fa.seek(0); fa.truncate(); json.dump(data, fa, ensure_ascii=False, indent=4)
                bot.reply_to(m, f"✅ {target} приступил к работе. Обновляю статус на сайте!")
            else:
                bot.reply_to(m, "❌ Агент не найден в системе.")
    bot.polling(none_stop=True)

# Запуск бота
if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")
st.subheader("📡 Живой поток взаимодействия агентов")

# Читаем данные с защитой
with open(FILES["agents"], "r", encoding="utf-8") as f:
    data = json.load(f)

for name, info in data.get("agents", {}).items():
    history = info.get("history", [])
    with st.chat_message("assistant" if name == "Аналитик" else "user"):
        st.write(f"**{name}**")
        for event in history[-3:]: # Последние 3 события
            st.caption(f"🔹 {event}")

time.sleep(1); st.rerun()
