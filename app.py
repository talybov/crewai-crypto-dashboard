import os
import time
import requests
import threading
import streamlit as st
import telebot

st.set_page_config(page_title="24/7 Smart AI Chatbot", page_icon="🤖")
st.title("🤖 Бессмертный ИИ-Ассистент")
st.write("Бот использует каскад из бесплатных моделей OpenRouter для обхода любых лимитов.")

# 1. Чтение токенов из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "")
TG_CHAT_ID = st.secrets.get("TG_CHAT_ID", "")
OR_KEY = st.secrets.get("OPENROUTER_API_KEY", "")

# Инициализируем историю чата на сервере
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Пул бесплатных моделей для автоматического перебора при лимитах
FREE_MODELS_POOL = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free"
]

# 2. Умная функция запроса с автоматической ротацией моделей
def ask_openrouter_with_fallback(messages_list):
    if not OR_KEY:
        return "❌ Ошибка: В Secrets не добавлен OPENROUTER_API_KEY!"
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "Content-Type": "application/json"
    }
    
    # Перебираем модели из нашего пула, если ловим лимиты
    for model_name in FREE_MODELS_POOL:
        payload = {
            "model": model_name,
            "messages": messages_list
        }
        try:
            print(f"[SYSTEM] Пробуем отправить запрос в модель: {model_name}")
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            
            # Если всё ок, забираем ответ и выходим из цикла
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            
            # Если поймали лимит (429) или ошибку сервера (5xx), идем к следующей модели
            elif response.status_code in [429, 502, 503]:
                print(f"[WARNING] Модель {model_name} перегружена (Код {response.status_code}). Пробуем альтернативу...")
                time.sleep(1)
                continue
            else:
                print(f"[ERROR] Сбой модели {model_name}: {response.text}")
                continue
        except Exception as e:
            print(f"[NET ERROR] Ошибка сети для {model_name}: {str(e)}")
            continue
            
    return "🤖 К сожалению, абсолютно все бесплатные нейросети OpenRouter сейчас перегружены мировым трафиком. Пожалуйста, повтори отправку сообщения через 1-2 минуты."

# 3. Функция анализа рынка с процентами
def start_light_analysis(bot):
    try:
        p_msg = bot.send_message(TG_CHAT_ID, "⏳ *Анализ запущен:* [▓░░░░░░░░░] 10%")
        time.sleep(0.3)
        
        try: bot.edit_message_text("⏳ *Сбор данных ИИ:* [▓▓▓▓▓░░░░░] 50%", TG_CHAT_ID, p_msg.message_id)
        except: pass
        
        prompt = "Проанализируй текущую ситуацию на рынке Bitcoin (BTC). Дай рекомендацию КУПИТЬ/ПРОДАТЬ/ДЕРЖАТЬ и объясни решение в 3-4 предложениях на русском языке."
        messages = [{"role": "user", "content": prompt}]
        
        res = ask_openrouter_with_fallback(messages)
        
        try: bot.edit_message_text("✅ *Готово:* [▓▓▓▓▓▓▓▓▓▓] 100%", TG_CHAT_ID, p_msg.message_id)
        except: pass
        time.sleep(0.3)
        
        try: bot.delete_message(TG_CHAT_ID, p_msg.message_id)
        except: pass
        
        return res
    except Exception as e:
        return f"❌ Ошибка анализа: {str(e)}"

# 4. Инициализация и запуск фонового Telegram-бота
@st.cache_resource(show_spinner=False)
def get_global_bot():
    bot_instance = telebot.TeleBot(TG_TOKEN)
    try:
        bot_instance.remove_webhook()
        time.sleep(1)
    except: pass
    return bot_instance

if TG_TOKEN:
    bot = get_global_bot()

    @bot.message_handler(commands=['start', 'clear'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            st.session_state.chat_history = []
            bot.reply_to(message, "👋 Привет! Я твой бессмертный ИИ-партнер.\n\n"
                                  "• Напиши **Анализ** для проверки рынка.\n"
                                  "• Пиши **любой текст**, чтобы поболтать на свободные темы.")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        if str(message.chat.id) == TG_CHAT_ID:
            user_text = message.text
            user_text_lower = user_text.lower().strip()
            
            if user_text_lower in ["анализ", "analyze", "/analyze"]:
                report = start_light_analysis(bot)
                bot.send_message(TG_CHAT_ID, f"📊 *Результаты анализа Биткоина:*\n\n{report}")
                return

            bot.send_chat_action(TG_CHAT_ID, 'typing')

            st.session_state.chat_history.append({"role": "user", "content": user_text})
            if len(st.session_state.chat_history) > 20:
                st.session_state.chat_history = st.session_state.chat_history[-20:]

            # Запускаем поиск ответа через каскад моделей
            ai_response = ask_openrouter_with_fallback(st.session_state.chat_history)

            # Если ответ успешный (не содержит финальной ошибки перегрузки всего пула)
            if "абсолютно все бесплатные нейросети" in ai_response:
                bot.send_message(TG_CHAT_ID, ai_response)
                st.session_state.chat_history.pop() # удаляем реплику, раз не ответили
            else:
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                bot.send_message(TG_CHAT_ID, ai_response)

    def run_bot_safe(bot_to_run):
        while True:
            try: bot_to_run.polling(none_stop=True, timeout=20)
            except: time.sleep(3)

    if "bot_thread_alive" not in st.session_state:
        t = threading.Thread(target=run_bot_safe, args=(bot,))
        t.daemon = True
        t.start()
        st.session_state.bot_thread_alive = True

    st.success("✅ Защищенный бот успешно перезапущен!")
else:
    st.warning("⚠️ Заполните Secrets на Streamlit.")
