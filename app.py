import os, time, requests, json, threading, streamlit as st, telebot, speech_recognition as sr, io, re
from pydub import AudioSegment

MEMORY_FILE = "bot_memory.json"

# --- ЛОГИКА ПАМЯТИ ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {
        "rules": "Ты — главный ИИ-Архитектор. Твоя задача — координировать рой агентов.",
        "agents": {
            "Аналитик": {"task": "Анализ BTC/ETH/SOL через OpenRouter"},
            "Метеоролог": {"task": "Мониторинг погоды через wttr.in"}
        },
        "history": []
    }

def save_memory(data):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

# --- МОДУЛИ АГЕНТОВ ---
def agent_analyst():
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}", "Content-Type": "application/json"}
    payload = {"model": "google/gemini-2.0-flash-exp:free", "messages": [{"role": "user", "content": "Дай краткий анализ рынка BTC и ETH."}]}
    res = requests.post(url, json=payload, headers=headers).json()
    return res['choices'][0]['message']['content']

def agent_weather(city):
    res = requests.get(f"https://wttr.in/{city}?format=3").text
    return f"Метеоролог сообщает: {res}"

# --- ОСНОВНОЙ БОТ ---
@st.cache_resource
def start_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(commands=['swarm'])
    def list_agents(m):
        mem = load_memory()
        bot.reply_to(m, f"🐝 Рой в строю: {json.dumps(mem['agents'], ensure_ascii=False)}")

    @bot.message_handler(func=lambda m: True)
    def handle_all(m):
        if str(m.chat.id) != str(st.secrets["TG_CHAT_ID"]): return
        mem = load_memory()
        text = m.text.lower()
        
        # Диспетчеризация
        if "анализ" in text:
            ans = agent_analyst()
        elif "погода" in text:
            city = text.replace("погода", "").strip() or "Москва"
            ans = agent_weather(city)
        else:
            # Общение с главным ИИ
            url = "https://api.cohere.com/v1/chat"
            headers = {"Authorization": f"Bearer {st.secrets['COHERE_API_KEY']}", "Content-Type": "application/json"}
            payload = {"model": "command-r-08-2024", "message": m.text, "preamble": mem["rules"], "chat_history": mem["history"][-10:]}
            ans = requests.post(url, json=payload, headers=headers).json().get("text", "...")
            
            mem["history"].append({"role": "USER", "message": m.text})
            mem["history"].append({"role": "CHATBOT", "message": ans})
            save_memory(mem)
            
        bot.send_message(m.chat.id, ans)

    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    return bot

if "TG_TOKEN" in st.secrets:
    start_bot()
    st.write("### Рой агентов активен.")
