import os
import time
import requests
import threading
import streamlit as st
import telebot
import speech_recognition as sr
from pydub import AudioSegment
import io

st.set_page_config(page_title="24/7 Dual AI Bot", page_icon="🤖")
st.title("🤖 Изолированный ИИ-Ассистент")
st.write("Свободное общение + голосовые сообщения через Cohere Command.")

# 1. Чтение токенов
TG_TOKEN = st.secrets.get("TG_TOKEN", "")
TG_CHAT_ID = str(st.secrets.get("TG_CHAT_ID", "")).strip()
OR_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
COHERE_KEY = st.secrets.get("COHERE_API_KEY", "")

if "cohere_history" not in st.session_state:
    st.session_state.cohere_history = []

# 2. OpenRouter — анализ BTC
def ask_openrouter_analysis():
    if not OR_KEY: return "❌ Нет OPENROUTER_API_KEY"
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
    except:
        pass
    return "🤖 Лимиты OpenRouter заняты. Попробуй позже!"

# 3. Cohere — свободное общение
def ask_cohere_chat(user_message):
    if not COHERE_KEY:
        return "❌ Нет COHERE_API_KEY!"
    url = "https://api.cohere.com/v1/chat"
    headers = {"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "command-r",
        "message": user_message,
        "chat_history": st.session_state.cohere_history,
        "preamble": "Ты — продвинутый ИИ-инженер и партнёр пользователя. Вы вместе разрабатываете систему ИИ-агентов. Отвечай кратко, дружелюбно, только на русском языке."
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            result = response.json()
            ai_
