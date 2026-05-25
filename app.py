import os, time, requests, json, threading, streamlit as st, telebot
from telebot import TeleBot

# --- КОНФИГ ПАМЯТИ ---
MEMORY_FILE = "bot_memory.json"

def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {"rules": "Ты — профессиональный ИИ-ассистент.", "history": []}

def save_memory(data):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

# --- МОДУЛИ ---
def ask_cohere(text, mem):
    try:
        url = "https://api.cohere.com/v1/chat"
        headers = {"Authorization": f"Bearer {st.secrets['COHERE_API_KEY']}", "Content-Type": "application/json"}
        payload = {"model": "command-r-08-2024", "message": text, "preamble": mem["rules"], "chat_history": mem["history"][-10:]}
        res = requests.post(url, json=payload, headers=headers, timeout=20).json()
        return res.get("text", "Извини, я немного задумался...")
    except Exception as e:
        return f"Ошибка связи: {e}"

# --- ЗАПУСК БОТА ---
@st.cache_resource
def start_bot():
    bot = TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(commands=['save'])
    def set_rules(m):
        mem = load_memory()
        mem["rules"] = m.text.replace("/save", "").strip()
        save_memory(mem)
        bot.reply_to(m, "✅ Инструкция принята.")

    @bot.message_handler(func=lambda m: True)
    def handle_all(m):
        if str(m.chat.id) != str(st.secrets["TG_CHAT_ID"]): return
        mem = load_memory()
        ans = ask_cohere(m.text, mem)
        
        # Обновление памяти
        mem["history"].append({"role": "USER", "message": m.text})
        mem["history"].append({"role": "CHATBOT", "message": ans})
        save_memory(mem)
            
        bot.send_message(m.chat.id, ans)

    def run():
        while True:
            try: bot.polling(none_stop=True)
            except: time.sleep(5)
            
    threading.Thread(target=run, daemon=True).start()
    return bot

if "TG_TOKEN" in st.secrets:
    start_bot()
    st.write("### Бот работает в безопасном режиме.")
