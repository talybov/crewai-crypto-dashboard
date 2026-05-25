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

TG_TOKEN = st.secrets.get("TG_TOKEN", "")
TG_CHAT_ID = str(st.secrets.get("TG_CHAT_ID", "")).strip()
OR_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
COHERE_KEY = st.secrets.get("COHERE_API_KEY", "")

if "cohere_history" not in st.session_state:
    st.session_state.cohere_history = []

def ask_openrouter_analysis():
    if not OR_KEY:
        return "❌ Нет OPENROUTER_API_KEY"
    url = "https://openrouter.ai/api/v1/chat/completion
