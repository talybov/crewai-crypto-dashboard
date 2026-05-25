import os
import time
import requests
import threading
import streamlit as st
import telebot

st.set_page_config(page_title="24/7 Smart AI Chatbot", page_icon="🤖")
st.title("🤖 Универсальный ИИ-Ассистент V3 (Safe Mode)")
st.write("Бот запущен в режиме безопасного вывода текста.")

# 1. Чтение токенов из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "")
TG_CHAT_ID = str(st.secrets.get("TG_CHAT_ID", "")).strip()
OR_KEY = st.secrets.get("OPENROUTER_API_KEY", "")

# Инициализируем историю чата
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

FREE_MODELS_POOL = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free"
]

# 2. Функция запроса к OpenRouter
def ask_openrouter_with_fallback(messages_list):
    if not OR_KEY:
        return "❌ Ошибка: В Secrets не добавлен OPENROUTER_API_KEY!"
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "Content-Type": "application/json"
    }
    
    for model_name in FREE_MODELS_POOL:
        payload = {"model": model_name, "messages": messages_list}
        try:
            print(f"[SYSTEM] Запрос в модель: {model_name}")
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code in [429, 502, 503]:
                print(f"[LIMIT] Модель {model_name} занята. Идем дальше...")
                time.sleep(1)
                continue
        except Exception as e:
            print(f"[NET ERROR] {model_name}: {str(e)}")
            continue
            
    return "🤖 Все бесплатные нейросети сейчас перегружены. Попробуй через минуту."

# 3. Функция быстрого анализа рынка
def start_light_analysis(bot, chat_id):
    try:
        # Отправляем обычным текстом БЕЗ макдауна, чтобы избежать сбоев 400
        p_msg = bot.send_message(chat_id, "⏳ Анализ запущен: [▓░░░░░░░░░] 10%")
        time.sleep(0.3)
        
        try: bot.edit_message_text("⏳ Сбор данных ИИ: [▓▓▓▓▓░░░░░] 50%", chat_id, p_msg.message_id)
        except: pass
        
        prompt = "Проанализируй текущую ситуацию на рынке Bitcoin (BTC). Дай рекомендацию КУПИТЬ/ПРОДАТЬ/ДЕРЖАТЬ и объясни решение в 3-4 предложениях на русском языке."
        messages = [{"role": "user", "content": prompt}]
        
        res = ask_openrouter_with_fallback(messages)
        
        try: bot.delete_message(chat_id, p_msg.message_id)
        except: pass
        
        return res
    except Exception as e:
        return f"❌ Ошибка анализа: {str(e)}"

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
        # Если ты нажал старт — бот покажет твой РЕАЛЬНЫЙ ID, проверим его
        current_id = str(message.chat.id)
        st.session_state.chat_history = []
        bot.reply_to(message, f"👋 Привет! Твой реальный ID чата: {current_id}\n\n"
                              f"В Secrets сейчас записан ID: {TG_CHAT_ID}\n\n"
                              "Если они совпадают, просто напиши мне 'Анализ' или любой текст!")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        current_id = str(message.chat.id)
        
        # Если ID не совпадает с Secrets, бот НЕ молчит, а честно говорит об этом!
        if current_id != TG_CHAT_ID:
            bot.reply_to(message, f"🔒 Доступ заблокирован. Твой ID ({current_id}) не совпадает с ID в Secrets ({TG_CHAT_ID}).")
            return

        user_text = message.text
        user_text_lower = user_text.lower().strip()
        
        if user_text_lower in ["анализ", "analyze", "/analyze"]:
            report = start_light_analysis(bot, current_id)
            # Отправка без parse_mode, чтобы текст гарантированно дошел
            bot.send_message(current_id, f"📊 Результаты анализа Биткоина:\n\n{report}")
            return

        bot.send_chat_action(current_id, 'typing')

        st.session_state.chat_history.append({"role": "user", "content": user_text})
        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history = st.session_state.chat_history[-20:]

        ai_response = ask_openrouter_with_fallback(st.session_state.chat_history)

        if "все бесплатные нейросети" in ai_response:
            bot.send_message(current_id, ai_response)
            st.session_state.chat_history.pop()
        else:
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            # Отправка без parse_mode для стабильности
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

    st.success("✅ Безопасный контроллер успешно запущен!")
