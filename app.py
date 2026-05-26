import streamlit as st
import json
import os
import telebot
import threading
import time
import random

# Настройка страницы
st.set_page_config(page_title="Multi-Agent Swarm", layout="wide")

FILES = {"agents": "bot_memory.json"}

# --- БАЗОВЫЕ ФУНКЦИИ ---
def init_data():
    """Создает структуру роя, если её еще нет."""
    if not os.path.exists(FILES["agents"]):
        data = {
            "agents": {
                "Исследователь": {"status": "idle", "history": ["Готов к работе..."]},
                "Аналитик": {"status": "idle", "history": ["Готов к работе..."]},
                "Риск-менеджер": {"status": "idle", "history": ["Готов к работе..."]},
                "Разработчик": {"status": "idle", "history": ["Готов к работе..."]},
                "Менеджер": {"status": "idle", "history": ["Готов к работе..."]}
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- ЛОГИКА БОТА ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(func=lambda m: True)
    def handle_message(m):
        with open(FILES["agents"], "r+", encoding="utf-8") as fa:
            data = json.load(fa)
            # Переводим всех в статус работы
            for agent in data["agents"]:
                data["agents"][agent]["status"] = "working"
                data["agents"][agent]["history"].append(f"📥 Задача: {m.text[:20]}...")
            fa.seek(0); fa.truncate(); json.dump(data, fa, ensure_ascii=False, indent=4)
        bot.reply_to(m, "🚀 Рой запущен. Наблюдаю за прогрессом на дашборде!")

    bot.polling(none_stop=True)

# Запуск бота в фоне
if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ДАШБОРДА ---
st.title("🛰 Центр Управления Роем")
st.markdown("---")

with open(FILES["agents"], "r", encoding="utf-8") as f:
    data = json.load(f)

# Визуальная сетка агентов
cols = st.columns(5)
agent_names = list(data["agents"].keys())

for i, name in enumerate(agent_names):
    info = data["agents"][name]
    with cols[i]:
        st.subheader(name)
        if info["status"] == "working":
            st.warning("⚠️ В работе...")
            # Имитация работы
            prog = st.progress(0)
            for p in range(100):
                prog.progress(p + 1)
            # Сброс статуса после завершения
            data["agents"][name]["status"] = "idle"
        else:
            st.success("🟢 Свободен")
        
        # История
        st.caption("История:")
        for entry in info["history"][-3:]:
            st.text(f"• {entry}")

# Сохраняем сброшенные статусы
with open(FILES["agents"], "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

# Автообновление для "живой" картинки
time.sleep(1)
st.rerun()
