import os
import time
import requests
import threading
import streamlit as st
import telebot

st.set_page_config(page_title="24/7 Dual AI Bot", page_icon="🤖")
st.title("🤖 Изолированный ИИ-Ассистент")
st.write("Свободное общение переведено на выделенный шлюз Cohere Command.")

# 1. Чтение токенов из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "")
TG_CHAT_ID = str(st.secrets.get("TG_CHAT_ID", "")).strip()
OR_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
COHERE_KEY = st.secrets.get("COHERE_API_KEY", "")

# Инициализируем историю чата для Cohere (у Cohere свой формат истории)
if "cohere_history" not in st.session_state:
    st.session_state.cohere_history = []

# 2. Запрос к OpenRouter (СТРОГО ДЛЯ АНАЛИЗА)
def ask_openrouter_analysis():
    if not OR_KEY: return "❌ Ошибка: Нет OPENROUTER_API_KEY"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [{"role": "user", "content": "Проанализируй текущую ситуацию на рынке Bitcoin (BTC). Дай рекомендацию КУПИТЬ/ПРОДАТЬ/ДЕРЖАТЬ и объясни решение в 3-4 предложениях на русском языке."}]
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        if res.status_code == 200: return res.json()['choices'][0]['message']['content']
    except: pass
    return "🤖 Лимиты OpenRouter сейчас заняты. Давай пообщаемся на другие темы!"

# 3. ПРЯМОЙ запрос к Cohere для свободного общения (Никаких лимитов!)
def ask_cohere_chat(user_message):
    if not COHERE_KEY:
        return "❌ Ошибка: В Secrets не добавлен COHERE_API_KEY!"
        
    url = "https://api.cohere.com/v1/chat"
    headers = {
        "Authorization": f"Bearer {COHERE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Формируем тело запроса с историей диалога по правилам Cohere
    payload = {
        "model": "command-r",
        "message": user_message,
        "chat_history": st.session_state.cohere_history,
        "preamble": "Ты — продвинутый ИИ-инженер, партнер и коллега пользователя. Вы вместе разрабатываете систему ИИ-агентов. Отвечай кратко, емко, дружелюбно и только на русском языке."
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            result = response.json()
            ai_text = result.get("text", "")
            
            # Сохраняем в память для контекста следующей реплики
            st.session_state.cohere_history.append({"role": "USER", "message": user_message})
            st.session_state.cohere_history.append({"role": "CHATBOT", "message": ai_text})
            
            # Держим в памяти последние 15 реплик
            if len(st.session_state.cohere_history) > 15:
                st.session_state.cohere_history = st.session_state.cohere_history[-15:]
                
            return ai_text
        else:
            return f"⚠️ Ошибка выделенного шлюза (Код {response.status_code})"
    except Exception as e:
        return f"💥 Сбой сети при общении: {str(e)}"

# 4. Инициализация фонового Telegram-бота
@st.cache_resource(show_spinner=False)
def get_global_bot():
    bot_instance = telebot.TeleBot(TG_TOKEN)
    try: bot_instance.remove_webhook()
    except: pass
    return bot_instance

if TG_TOKEN:
    bot = get_global_bot()

    @bot.message_handler(commands=['start', 'clear'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            st.session_state.cohere_history = []
            bot.reply_to(message, "👋 Привет! Твой выделенный ИИ-собеседник на связи.\n\n"
                                  "• Напиши **Анализ** — пойдет запрос по Биткоину.\n"
                                  "• Пиши **любой другой текст** — мы общаемся через чистый канал Cohere Command.")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        current_id = str(message.chat.id)
        if current_id != TG_CHAT_ID: return

        user_text = message.text
        user_text_lower = user_text.lower().strip()
        
        # Запрос Анализа рынка
        if user_text_lower in ["анализ", "analyze", "/analyze"]:
            p_msg = bot.send_message(current_id, "⏳ Анализ запущен: [▓▓▓▓░░░░░░] 40%")
            report = ask_openrouter_analysis()
            try: bot.delete_message(current_id, p_msg.message_id)
            except: pass
            bot.send_message(current_id, f"📊 Результаты анализа Биткоина:\n\n{report}")
            return

        # Режим СВОБОДНОГО общения через независимый Cohere
        bot.send_chat_action(current_id, 'typing')
        ai_response = ask_cohere_chat(user_text)
        bot.send_message(current_id, ai_response)

    def run_bot_safe(bot_to_run):
        while True:
            try: bot_to_run.polling(none_stop=True, timeout=20)
            except: time.sleep(3)

    if "bot_thread_alive" not in st.session_state:
        t = threading.Thread(target=run_bot_safe, args=(bot,))
        t.daemon = True
        t.start()
        st.session_state.bot_thread_alive = True

    st.success("✅ Двухканальный бот успешно запущен!")
