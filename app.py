import streamlit as st
import telebot, json, os, time, threading

# --- КОНФИГ ---
MEMORY_FILE = "bot_memory.json"

# --- ЛОГИКА ДАННЫХ ---
def get_swarm_status():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f).get("agents", {})
    return {}

def update_agent_status(name, status):
    mem = get_swarm_status()
    if name in mem:
        mem[name]["status"] = status
        with open(MEMORY_FILE, "w") as f:
            json.dump({"agents": mem}, f)

# --- САЙТ (Streamlit Дашборд) ---
st.set_page_config(page_title="AI Swarm Control", layout="wide")
st.title("🚀 Центр Управления Роем")

col1, col2, col3 = st.columns(3)
agents = get_swarm_status()

# Визуализация агентов на сайте
for i, (name, info) in enumerate(agents.items()):
    with [col1, col2, col3][i % 3]:
        st.metric(label=name, value=info["status"], delta="Активен")

if st.button("Обновить статус"):
    st.rerun()

# --- БОТ (Telegram) ---
def run_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(commands=['status'])
    def send_status(m):
        status = get_swarm_status()
        msg = "\n".join([f"{k}: {v['status']}" for k, v in status.items()])
        bot.reply_to(m, f"📋 Статус роя:\n{msg}")

    bot.polling(none_stop=True)

# Запуск бота в фоне
if "TG_TOKEN" in st.secrets:
    threading.Thread(target=run_bot, daemon=True).start()
    
