import streamlit as st
import json
import os
import telebot
import threading
import time

FILES = {"agents": "bot_memory.json"}

def init_data():
    if not os.path.exists(FILES["agents"]):
        data = {"agents": {
            "Аналитик": {"history": ["Готов к работе..."]},
            "Исследователь": {"history": ["Готов к работе..."]},
            "Риск-менеджер": {"history": ["Готов к работе..."]},
            "Разработчик": {"history": ["Готов к работе..."]},
            "Менеджер": {"history": ["Готов к работе..."]}
        }}
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(func=lambda m: True)
    def handle_message(m):
        with open(FILES["agents"], "r+", encoding="utf-8") as fa:
            data = json.load(fa)
            
            # Полный конвейер из 5 ролей
            steps = {
                "Исследователь": f"🔍 Поиск инфо: {m.text}",
                "Аналитик": f"📊 Анализ данных по: {m.text}",
                "Риск-менеджер": f"🛡 Оценка рисков: {m.text}",
                "Разработчик": f"💻 Автоматизация процесса: {m.text}",
                "Менеджер": f"✅ Финализация отчета: {m.text}"
            }
            
            for agent, action in steps.items():
                if agent in data["agents"]:
                    data["agents"][agent].setdefault("history", []).append(f"🔹 {action}")
            
            fa.seek(0); fa.truncate(); json.dump(data, fa, ensure_ascii=False, indent=4)
            
        bot.reply_to(m, "🤖 Весь рой (5 агентов) взял задачу в работу!")

    bot.polling(none_stop=True)

if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")
st.write("Активный состав: 5 специалистов")

with open(FILES["agents"], "r", encoding="utf-8") as f:
    data = json.load(f)

# Отображаем всех пятерых
for name, info in data.get("agents", {}).items():
    with st.chat_message("assistant"):
        st.write(f"**{name}**")
        for event in info.get("history", [])[-3:]:
            st.caption(f"{event}")

time.sleep(1); st.rerun()
