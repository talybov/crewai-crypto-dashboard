import streamlit as st
import json, os, threading, telebot
import json
import os
import threading
import telebot
import time  # <--- ВОТ ЭТОГО СЛОВА НЕ ХВАТАЕТ
import datetime # Не забудь добавить этот импорт в начало файла
# --- 1. КОНФИГУРАЦИЯ ---
FILES = {
    "agents": "bot_memory.json",
    "tasks": "tasks_log.json"
}

# --- 2. ЯДРО СИСТЕМЫ (Работа с памятью) ---
def init_storage():
    """Создает файлы, если их нет."""
    if not os.path.exists(FILES["agents"]):
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump({"agents": {}}, f)
    if not os.path.exists(FILES["tasks"]):
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)

def get_data(key):
    with open(FILES[key], "r", encoding="utf-8") as f:
        return json.load(f)

# --- 3. ИНТЕРФЕЙС (Сайт) ---
st.set_page_config(page_title="Swarm Control", layout="wide")
init_storage()

st.title("🛰 Центр Управления Роем")

# Блок мониторинга
col1, col2 = st.columns(2)
with col1:
    st.subheader("Агенты")
   # --- ИНТЕРФЕЙС (Живой) ---
# Создаем контейнер, который будет постоянно обновляться
placeholder = st.empty()
# --- ИНИЦИАЛИЗАЦИЯ АГЕНТОВ (если они еще не созданы) ---
# --- ИНИЦИАЛИЗАЦИЯ АГЕНТОВ ---
def setup_initial_agents():
    if not os.path.exists(FILES["agents"]):
        data = {
            "agents": {
                "Аналитик": {"status": "💤 Спит", "task": "Ожидание"},
                "Менеджер": {"status": "💤 Спит", "task": "Ожидание"}
            }
        }
        with open(FILES["agents"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
# <--- Эта строка должна быть ровно здесь (без пробелов в начале)
setup_initial_agents()
# Вызываем функцию сразу при запуске
setup_initial_agents()
        }
    }
    with open("bot_memory.json", "w", encoding="utf-8") as f:
        json.dump(initial_data, f, ensure_ascii=False)
while True:
    with placeholder.container():
        # Добавляем индикатор времени, чтобы видеть, что сайт «дышит»
        st.write(f"⏰ Последнее обновление: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤖 Агенты")
            st.json(get_data("agents"))
            
        with col2:
            st.subheader("📝 Лог задач")
            st.json(get_data("tasks"))
    
    time.sleep(1) # Обновляем каждую секунду
    st.rerun()
    
    # Пауза 3 секунды перед обновлением данных
    time.sleep(3)
    # Перезапуск скрипта для считывания свежих данных из файлов
    st.rerun()
with col2:
    st.subheader("Лог задач")
    st.json(get_data("tasks"))

# --- 4. БОТ (Telegram) ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    
    # 1. Приветствие
    @bot.message_handler(commands=['start'])
    def start(m):
        bot.reply_to(m, "Рой готов к работе! Используй /add [задача] для добавления.")

    # 2. Добавление задачи
    @bot.message_handler(commands=['add'])
    def add_task(m):
        task_text = m.text.replace("/add", "").strip()
        if not task_text:
            bot.reply_to(m, "Укажи задачу после команды /add")
            return
        
        # Читаем файл
        with open(FILES["tasks"], "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Добавляем задачу
        data["tasks"].append({"task": task_text, "status": "Ожидает"})
        
        # Сохраняем
        with open(FILES["tasks"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        bot.reply_to(m, f"✅ Задача '{task_text}' добавлена в список!")
        
    bot.polling(none_stop=True)

if "TG_TOKEN" in st.secrets:
    threading.Thread(target=run_bot, daemon=True).start()
