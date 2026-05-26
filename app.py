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
    if not os.path.exists(FILES["agents"]):
        data = {"agents": {
            "Аналитик": {"history": ["Готов к работе..."]},
            "Риск-менеджер": {"history": ["Готов к работе..."]},
            "Менеджер": {"history": ["Ожидаю команды..."]}
        }}
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- ЛОГИКА ДИСПЕТЧЕРА ---
def route_task(text):
    text = text.lower()
    if "проанализируй" in text or "анализ" in text:
        return "Аналитик"
    if "риск" in text or "безопасность" in text:
        return "Риск-менеджер"
    return "Менеджер"

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(func=lambda m: True)
    def handle_message(m):
        target_agent = route_task(m.text)
        
        with open(FILES["agents"], "r+", encoding="utf-8") as fa:
            data = json.load(fa)
            
            # Добавляем событие
            msg = f"📥 Получил задачу: {m.text[:30]}..."
            data["agents"][target_agent]["history"].append(msg)
            
            fa.seek(0); fa.truncate(); json.dump(data, fa, ensure_ascii=False, indent=4)
            
        bot.reply_to(m, f"🤖 Диспетчер: передал задачу агенту **{target_agent}**")

    bot.polling(none_stop=True)

# Запуск
if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")
with open(FILES["agents"], "r", encoding="utf-8") as f:
    data = json.load(f)

for name, info in data["agents"].items():
    with st.chat_message("assistant"):
        st.write(f"**{name}**")
        for event in info.get("history", [])[-3:]:
            st.caption(f"🔹 {event}")

time.sleep(1); st.rerun()
