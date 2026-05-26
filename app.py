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
                "Исследователь": {"status": "Свободен", "history": ["Ожидание..."]},
                "Аналитик": {"status": "Свободен", "history": ["Ожидание..."]},
                "Риск-менеджер": {"status": "Свободен", "history": ["Ожидание..."]},
                "Разработчик": {"status": "Свободен", "history": ["Ожидание..."]},
                "Менеджер": {"status": "Свободен", "history": ["Ожидание..."]}
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- ЛОГИКА ЭКСПЕРТИЗЫ (Цепочка эстафеты) ---
def get_agent_result(role, previous_data):
    if role == "Исследователь": return f"Исследование: '{previous_data}' - найдены бычьи сигналы."
    if role == "Аналитик": return f"Анализ: '{previous_data}' - поддержка на $140."
    if role == "Риск-менеджер": return f"Риски: '{previous_data}' - стоп-лосс на $135."
    if role == "Разработчик": return f"Код: '{previous_data}' - бот настроен."
    if role == "Менеджер": return f"Итог: '{previous_data}' - Сделка одобрена."
    return previous_data

# --- БОТ ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])

    @bot.message_handler(func=lambda m: True)
    def handle_message(m):
        with open(FILES["agents"], "r+", encoding="utf-8") as fa:
            data = json.load(fa)
            
            # Запуск логической эстафеты
            current_context = m.text
            roles = ["Исследователь", "Аналитик", "Риск-менеджер", "Разработчик", "Менеджер"]
            
            for agent in roles:
                data["agents"][agent]["status"] = "В работе..."
                result = get_agent_result(agent, current_context)
                data["agents"][agent]["history"].append(f"🔹 {result}")
                current_context = result # Передача результата дальше
                
            # Сброс статусов
            for agent in roles:
                data["agents"][agent]["status"] = "Свободен"
            
            fa.seek(0); fa.truncate(); json.dump(data, fa, ensure_ascii=False, indent=4)
        
        bot.reply_to(m, "🤖 Рой успешно завершил цикл обработки задачи!")

    bot.polling(none_stop=True)

# Запуск бота в фоне
if "bot_started" not in st.session_state:
    threading.Thread(target=run_bot, daemon=True).start()
    st.session_state.bot_started = True

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")
st.markdown("---")

with open(FILES["agents"], "r", encoding="utf-8") as f:
    data = json.load(f)

# Отображение 5 колонок с агентами
cols = st.columns(5)
for i, (name, info) in enumerate(data["agents"].items()):
    with cols[i]:
        st.subheader(name)
        
        # Индикация статуса
        if info["status"] == "Свободен":
            st.success("🟢 Свободен")
        else:
            st.warning("⚠️ В работе...")
            
        st.write("**История:**")
        for event in info.get("history", [])[-4:]:
            st.caption(event)

# Автообновление для "живого" дашборда
time.sleep(2)
st.rerun()
