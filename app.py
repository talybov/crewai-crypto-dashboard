import streamlit as st
import json
import os
import time

# --- НАСТРОЙКИ ---
st.set_page_config(page_title="Swarm Dashboard", layout="wide")
DATA_FILE = "bot_memory.json"

# --- ИНИЦИАЛИЗАЦИЯ ---
def init_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "agents": {
                "Исследователь": {"status": "Свободен", "history": ["Старт системы..."]},
                "Аналитик": {"status": "Свободен", "history": ["Старт системы..."]},
                "Риск-менеджер": {"status": "Свободен", "history": ["Старт системы..."]},
                "Разработчик": {"status": "Свободен", "history": ["Старт системы..."]},
                "Менеджер": {"status": "Свободен", "history": ["Старт системы..."]}
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# --- ИНТЕРФЕЙС ---
st.title("🛰 Центр Управления Роем")

try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    cols = st.columns(5)
    for i, (name, info) in enumerate(data["agents"].items()):
        with cols[i]:
            st.subheader(name)
            st.success(info["status"])
            st.write("История:")
            for event in info.get("history", []):
                st.caption(event)
except Exception as e:
    st.error(f"Ошибка загрузки данных: {e}")

# Чтобы не было бесконечного цикла, если что-то не так
if st.button("Обновить статус"):
    st.rerun()
