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
            "Аналитик": {"history": ["Инициализация системы..."]},
            "Риск-менеджер": {"history": ["Ожидание данных..."]}
        }}
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(commands=['work'])
    def work_agent(m):
        target = m.text.replace("/work", "").strip()
        with open(FILES["agents"], "r+", encoding="utf-8") as fa:
            agents = json.load(fa)
            if target in agents["agents"]:
                msg = f"🧠 {target} начал обработку данных и передал эстафету коллеге."
                agents["agents"][target]["history"].append(msg)
                fa.seek(0); fa.truncate(); json.dump(agents, fa, ensure_ascii=False, indent=4)
                bot.reply_to(m, "✅ Задача в процессе, смотри трансляцию на сайте!")
            else:
                bot.reply_to(m, "❌ Агент не найден.")
    bot.polling(none_stop=True)

# Запуск бота
if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС «ТРАНСЛЯЦИЯ ОБЩЕНИЯ» ---
st.title("🛰 Центр Управления Роем")
st.subheader("📡 Живой поток взаимодействия агентов")

with open(FILES["agents"], "r", encoding="utf-8") as f:
    data = json.load(f)

# Красивое отображение «диалога»
for name, info in data["agents"].items():
    with st.chat_message("assistant" if name == "Аналитик" else "user"):
        st.write(f"**{name}**")
        for event in info["history"][-3:]: # Показываем последние 3 события
            st.caption(f"🔹 {event}")

time.sleep(1); st.rerun()
