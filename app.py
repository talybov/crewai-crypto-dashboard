import streamlit as st
import json
import os
import telebot
import threading
import time

# Настройка страницы
st.set_page_config(page_title="Multi-Agent Swarm", layout="wide")

FILES = {"agents": "bot_memory.json"}

# --- ИНИЦИАЛИЗАЦИЯ ДАННЫХ ---
def init_data():
    if not os.path.exists(FILES["agents"]):
        data = {
            "agents": {
                "Исследователь": {"status": "Свободен", "history": ["Готов к работе..."]},
                "Аналитик": {"status": "Свободен", "history": ["Готов к работе..."]},
                "Риск-менеджер": {"status": "Свободен", "history": ["Готов к работе..."]},
                "Разработчик": {"status": "Свободен", "history": ["Готов к работе..."]},
                "Менеджер": {"status": "Свободен", "history": ["Готов к работе..."]}
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- ЛОГИКА ЭКСПЕРТИЗЫ ---
def get_agent_result(role, previous_data):
    # Здесь логика, где агент реально "дополняет" предыдущие данные
    if role == "Исследователь": return f"Сбор данных: '{previous_data}' завершен. Найдены бычьи сигналы."
    if role == "Аналитик": return f"Тех. анализ: '{previous_data}'. Уровень поддержки найден."
    if role == "Риск-менеджер": return f"Аудит рисков: '{previous_data}'. Стопы установлены."
    if role == "Разработчик": return f"Автоматизация: '{previous_data}'. Скрипт готов к деплою."
    if role == "Менеджер": return f"Итоговое решение: '{previous_data}'. Проект одобрен."
    return previous_data

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(func=lambda m: True)
    def handle_message(m):
        with open(FILES["agents"], "r+", encoding="utf-8") as fa:
            data = json.load(fa)
            
            # Цепочка эстафеты
            current_context = m.text
            for agent in ["Исследователь", "Аналитик", "Риск-менеджер", "Разработчик", "Менеджер"]:
                data["agents"][agent]["status"] = "В работе..."
                result = get_agent_result(agent, current_context)
                data["agents"][agent]["history"].append(f"🔹 {result}")
                current_context = result
                data["agents"][agent]["status"] = "Свободен"
            
            fa.seek(0); fa.truncate(); json.dump(data, fa, ensure_ascii=False, indent=4)
        bot.reply_to(m, "🤖 Рой завершил логическую цепочку!")

    bot.polling(none_stop=True)

if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")
st.markdown("---")

with open(FILES["agents"], "r", encoding="utf-8") as f:
    data = json.load(f)

# Отображение 5 колонок
cols = st.columns(5)
for i, (name, info) in enumerate(data["agents"].items()):
    with cols[i]:
        st.subheader(name)
        status = info["status"]
        if status == "Свободен":
            st.success(status)
        else:
            st.warning(status)
            
        st.write("История:")
        for event in info.get("history", [])[-4:]:
            st.caption(event)

time.sleep(1)
st.rerun()
