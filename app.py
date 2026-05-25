import os
import time
import requests
import threading
import streamlit as st
import telebot
import speech_recognition as sr
from pydub import AudioSegment
import io
import re

st.set_page_config(page_title="24/7 Smart Brain Bot", page_icon="🧠")
st.title("🧠 Бессмертный ИИ-Ассистент V5")
st.write("Стабильный режим: Крипта + Голос + Реальная Погода.")

# 1. Чтение токенов из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "")
TG_CHAT_ID = str(st.secrets.get("TG_CHAT_ID", "")).strip()
OR_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
COHERE_KEY = st.secrets.get("COHERE_API_KEY", "")

# Глобальная история и лок для потоков
if "global_cohere_history" not in st.experimental_singleton if hasattr(st, "experimental_singleton") else globals():
    cohere_history = []
else:
    cohere_history = []
    
history_lock = threading.Lock()


# 2. Функция получения РЕАЛЬНОЙ погоды
def get_weather(city_name):
    try:
        # Запрашиваем погоду в формате JSON на русском языке
        url = f"https://wttr.in/{city_name}?format=j1&lang=ru"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            
            temp = current['temp_C'] # Температура в Цельсиях
            desc = current['lang_ru'][0]['value'] # Описание (ясно, пасмурно и т.д.)
            humidity = current['humidity'] # Влажность
            wind = current['windspeedKmph'] # Скорость ветра
            
            report = (
                f"🌍 **Реальные данные погоды ({city_name.capitalize()}):**\n"
                f"🌡 Температура: {temp}°C\n"
                f"☁️ На улице: {desc}\n"
                f"💧 Влажность: {humidity}%\n"
                f"💨 Ветер: {wind} км/ч\n"
            )
            return report
        return None
    except Exception as e:
        print(f"[WEATHER ERROR] {str(e)}")
        return None


# 3. Запрос к Cohere (Свободное общение)
def ask_cohere_chat(user_message):
    global cohere_history
    if not COHERE_KEY:
        return "❌ Нет COHERE_API_KEY в Secrets!"
    url = "https://api.cohere.com/v1/chat"
    headers = {"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json"}
    
    with history_lock:
        current_history = list(cohere_history)
        
    system_preamble = (
        "Ты — сверхинтеллектуальный универсальный ИИ-ассистент, главный инженер и крипто-аналитик. "
        "Ты обладаешь глубочайшими знаниями во всех областях науки, IT, программирования и финансов. "
        "Твоя цель — давать максимально развернутые, экспертные, детальные и умные ответы на любые вопросы пользователя. "
        "При этом ты остаешься главным архитектором вашей совместной крипто-экосистемы ИИ-агентов. "
        "Ты помнишь, что вы строите систему анализа монет (BTC, ETH, SOL) с будущей интеграцией CoinGecko API и paper trading. "
        "Отвечай всегда строго на русском языке, содержательно, авторитетно и по делу, добавляя ценные инсайты."
    )
        
    payload = {
        "model": "command-r-08-2024",
        "message": user_message,
        "chat_history": current_history,
        "preamble": system_preamble
    }
    try:
        print(f"[SYSTEM] Отправка запроса в Cohere...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            ai_text = response.json().get("text", "Нет ответа")
            with history_lock:
                cohere_history.append({"role": "USER", "message": user_message})
                cohere_history.append({"role": "CHATBOT", "message": ai_text})
                if len(cohere_history) > 20:
                    cohere_history = cohere_history[-20:]
            return ai_text
        else:
            return f"⚠️ Ошибка API Cohere (Код {response.status_code})."
    except Exception as e:
        return f"💥 Исключение сети: {str(e)}"


# 4. Запрос к OpenRouter (ЭКСПРЕСС-АНАЛИЗ BTC)
def ask_openrouter_analysis():
    if not OR_KEY:
        return "❌ Нет OPENROUTER_API_KEY"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [{"role": "user", "content": "Проанализируй рынок Bitcoin. Дай рекомендацию КУПИТЬ/ПРОДАТЬ/ДЕРЖАТЬ, объясни в 3-4 предложениях на русском."}]
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
        return f"⚠️ Ошибка OpenRouter: {res.status_code}"
    except Exception as e:
        return f"💥 Ошибка OpenRouter: {str(e)}"


# 5. Распознавание голоса
def transcribe_voice(file_id, bot_instance):
    try:
        file_info = bot_instance.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TG_TOKEN}/{file_info.file_path}"
        audio_data = requests.get(file_url).content
        ogg_audio = AudioSegment.from_file(io.BytesIO(audio_data), format="ogg")
        wav_buffer = io.BytesIO()
        ogg_audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_buffer) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="ru-RU")
    except Exception as e:
        print(f"[VOICE ERROR] {str(e)}")
        return None


# 6. ГЛОБАЛЬНЫЙ ЗАПУСК БОТА СЕРВЕРА
@st.cache_resource(show_spinner=False)
def init_and_run_bot():
    bot_instance = telebot.TeleBot(TG_TOKEN)
    try:
        bot_instance.remove_webhook()
        time.sleep(1)
    except:
        pass

    @bot_instance.message_handler(commands=['start', 'clear'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            global cohere_history
            with history_lock:
                cohere_history.clear()
            bot_instance.send_message(message.chat.id,
                "👋 Привет! Твой супер-бот полностью обновлен.\n\n"
                "• Напиши 'Погода Москва' (или любой город) — выведу реальный прогноз\n"
                "• Напиши 'Анализ' — быстрый сигнал по BTC\n"
                "• Напиши 'Как дела у агентов' — статус крипто-проекта\n"
                "• Любой текст или Голосовое — свободное общение с ИИ.")

    # Обработка входящего текста или распознанного голоса
    def process_user_logic(chat_id, text_message):
        user_text_lower = text_message.lower().strip()
        
        # 1. ТРИГГЕР ПОГОДЫ
        if "погода" in user_text_lower:
            # Извлекаем название города (всё, что идет после слова "погода")
            city = "москва" # по умолчанию
            match = re.search(r"погода\s+([а-яёa-z\-]+)", user_text_lower)
            if match:
                city = match.group(1)
            
            bot_instance.send_chat_action(chat_id, 'typing')
            weather_data = get_weather(city)
            
            if weather_data:
                # Отдаем погоду нейросети, чтобы она прокомментировала её в своем стиле
                ai_comment_prompt = f"Вот реальная погода в городе {city}: {weather_data}. Напиши краткий, остроумный комментарий к этой погоде в своем фирменном стиле крипто-инженера."
                ai_comment = ask_cohere_chat(ai_comment_prompt)
                
                final_msg = f"{weather_data}\n💭 **ИИ-Комментарий:** {ai_comment}"
                bot_instance.send_message(chat_id, final_msg)
            else:
                bot_instance.send_message(chat_id, f"❌ Не удалось получить данные погоды для города '{city}'. Проверь название.")
            return

        # 2. ТРИГГЕР АНАЛИЗА
        if user_text_lower in ["анализ", "analyze", "/analyze"]:
            p_msg = bot_instance.send_message(chat_id, "⏳ Анализирую рынок...")
            report = ask_openrouter_analysis()
            try: bot_instance.delete_message(chat_id, p_msg.message_id)
            except: pass
            bot_instance.send_message(chat_id, f"📊 Анализ Bitcoin:\n\n{report}")
            return
            
        # 3. ТРИГГЕР СТАТУСА АГЕНТОВ
        if "как дела у агентов" in user_text_lower or "статус агентов" in user_text_lower:
            status_report = (
                "🤖 Отчёт по крипто-экосистеме ИИ-агентов:\n\n"
                "1. 📈 Агент базового анализа рынка (OpenRouter): Активен. Собирает экспресс-отчеты по BTC через Gemini 2.0 Flash.\n"
                "2. 🗣 Командный интерфейс (Cohere): Стабилен на Command R. Успешно подключен метео-модуль wttr.in.\n"
                "3. 📊 Модуль мульти-монет (В планах): Внедрение реальных данных (ETH, SOL) через CoinGecko API.\n"
                "4. 💼 Торговый агент (Paper Trading): Симуляция сделок.\n\n"
                "⚡ Инфраструктура готова. Какой шаг делаем дальше?"
            )
            bot_instance.send_message(chat_id, status_report)
            return
            
        # 4. ОБЫЧНЫЙ ДИАЛОГ
        bot_instance.send_chat_action(chat_id, 'typing')
        ai_response = ask_cohere_chat(text_message)
        bot_instance.send_message(chat_id, ai_response)

    @bot_instance.message_handler(content_types=['voice'])
    def handle_voice(message):
        if str(message.chat.id) != TG_CHAT_ID: return
        try:
            bot_instance.send_chat_action(message.chat.id, 'typing')
            text = transcribe_voice(message.voice.file_id, bot_instance)
            if text:
                print(f"[VOICE] Распознано: {text}")
                process_user_logic(message.chat.id, text)
            else:
                bot_instance.send_message(message.chat.id, "❌ Не смог распознать звук в голосовом.")
        except Exception as e:
            bot_instance.send_message(message.chat.id, f"💥 Ошибка голос: {str(e)}")

    @bot_instance.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        if str(message.chat.id) != TG_CHAT_ID: return
        try:
            user_text = message.text or ""
            process_user_logic(message.chat.id, user_text)
        except Exception as e:
            bot_instance.send_message(message.chat.id, f"💥 Ошибка обработки: {str(e)}")

    def run_polling():
        print("[SYSTEM] Фоновый поток запущен!")
        while True:
            try:
                bot_instance.polling(none_stop=True, timeout=20, long_polling_timeout=20)
            except Exception as e:
                print(f"[POLLING ERROR] Сбой сети: {str(e)}")
                time.sleep(5)

    t = threading.Thread(target=run_polling)
    t.daemon = True
    t.start()
    return bot_instance


if TG_TOKEN:
    bot = init_and_run_bot()
    st.success("✅ Метео-модуль успешно интегрирован в архитектуру бота!")
else:
    st.error("❌ Заполните TG_TOKEN в Secrets!")
