import os, time, requests, json, threading, streamlit as st, telebot, speech_recognition as sr, io, re
from pydub import AudioSegment

# --- КОНФИГ ПАМЯТИ ---
MEMORY_FILE = "bot_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"rules": "Ты — главный ИИ-инженер, крипто-аналитик и партнер пользователя. Твоя цель — анализ монет (BTC, ETH, SOL) и симуляция трейдинга.", "history": []}

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- МОДУЛИ ---
def ask_cohere(text, mem):
    url = "https://api.cohere.com/v1/chat"
    headers = {"Authorization": f"Bearer {st.secrets['COHERE_API_KEY']}", "Content-Type": "application/json"}
    payload = {"model": "command-r-08-2024", "message": text, "preamble": mem["rules"], "chat_history": mem["history"][-15:]}
    res = requests.post(url, json=payload, headers=headers).json()
    return res.get("text", "Ошибка API")

def get_crypto_analysis():
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}", "Content-Type": "application/json"}
    payload = {"model": "google/gemini-2.0-flash-exp:free", "messages": [{"role": "user", "content": "Анализ BTC, ETH, SOL. Кратко, по делу."}]}
    return requests.post(url, json=payload, headers=headers).json()['choices'][0]['message']['content']

def get_weather(city):
    try:
        res = requests.get(f"https://wttr.in/{city}?format=3").text
        return f"Погода в {city}: {res}"
    except: return "Не удалось узнать погоду."

# --- ЗАПУСК БОТА ---
@st.cache_resource
def start_bot():
    bot = telebot.TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(commands=['save'])
    def set_rules(m):
        mem = load_memory()
        mem["rules"] = m.text.replace("/save", "").strip()
        save_memory(mem)
        bot.reply_to(m, "✅ Установки приняты, я подстроился под тебя.")

    @bot.message_handler(func=lambda m: True)
    def handle_all(m):
        if str(m.chat.id) != str(st.secrets["TG_CHAT_ID"]): return
        
        mem = load_memory()
        text = m.text.lower()
        
        # Маршрутизация запросов
        if "анализ" in text:
            ans = get_crypto_analysis()
        elif "погода" in text:
            city = text.replace("погода", "").strip() or "Москва"
            ans = get_weather(city)
        else:
            ans = ask_cohere(m.text, mem)
            mem["history"].append({"role": "USER", "message": m.text})
            mem["history"].append({"role": "CHATBOT", "message": ans})
            save_memory(mem)
            
        bot.send_message(m.chat.id, ans)

    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    return bot

if "TG_TOKEN" in st.secrets:
    start_bot()
    st.write("### Бот активен. Память работает через `bot_memory.json`.")
