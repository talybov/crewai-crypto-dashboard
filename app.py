import os
import sys
import time
import streamlit as st

# 1. Отключаем проблемный трекер OpenTelemetry до импорта CrewAI
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

# 2. Настройка стилей страницы Streamlit
st.set_page_config(page_title="Multi-Key Crypto AI Dashboard", page_icon="📊", layout="wide")

st.title("📊 Рой ИИ-Агентов с ротацией и паузами")
st.subheader("Система обхода лимитов для бесплатного тарифа Gemini")

# 3. Боковое меню для ввода НЕСКОЛЬКИХ ключей
st.sidebar.markdown("### 🔑 Пул API-ключей Gemini")
keys_input = st.sidebar.text_area(
    "Вставь сюда свои API-ключи (каждый ключ с новой строки):", 
    height=150, 
    placeholder="AIzaSy...\nAIzaSy...\nAIzaSy..."
)

st.sidebar.markdown("""
### 💡 Как это работает?
Программа создаст из ключей очередь. Если один ключ или IP-адрес упрется в лимит, система сделает паузу 10 секунд, переключится на следующий ключ и продолжит работу без вылета!
""")

# Разделение экрана на две колонки
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🤖 Управление Роем")
    start_button = st.button("🚀 Запустить анализ Биткоина", use_container_width=True)
    
    status_area = st.empty()
    result_area = st.empty()

with col2:
    st.markdown("### ⚙️ Внутренние мысли и шаги Агентов")
    log_area = st.empty()

# 4. Класс для перехвата логов из терминала и вывода их на экран
class StreamlitStdoutTrigger:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.text = ""
    def write(self, bytes_data):
        self.text += bytes_data
        clean_text = self.text.replace("Entering New CrewAgentExecutor Chain", "🤖 Агент переходит к следующему шагу...")
        self.placeholder.code(clean_text)
    def flush(self):
        pass

# 5. Менеджер ротации ключей
class KeyRotator:
    def __init__(self, keys_list):
        self.keys = [k.strip() for k in keys_list if k.strip()]
        self.index = 0
    
    def get_current_key(self):
        if not self.keys:
            return None
        return self.keys[self.index]
    
    def rotate(self):
        if len(self.keys) > 1:
            self.index = (self.index + 1) % len(self.keys)
            return True
        return False

# 6. Логика работы при нажатии на кнопку
if start_button:
    # Разбираем введенные ключи по строкам
    api_keys = keys_input.split("\n") if keys_input else []
    rotator = KeyRotator(api_keys)
    
    if not rotator.keys:
        st.error("❌ Сначала вставь хотя бы один API-ключ Gemini в боковое меню!")
    else:
        current_key = rotator.get_current_key()
        os.environ["GEMINI_API_KEY"] = current_key

        status_area.info(f"⏳ Агент начинает анализ рынка (Используется ключ {rotator.index + 1} из {len(rotator.keys)})...")

        # Функция для запуска Crew с возможностью перезапуска при ошибке 429
        def run_crew_with_retry(max_attempts=5):
            for attempt in range(max_attempts):
                try:
                    # Настраиваем модель на текущем активном ключе
                    active_key = rotator.get_current_key()
                    os.environ["GEMINI_API_KEY"] = active_key
                    
                    custom_llm = LLM(
                        model="gemini/gemini-2.0-flash",
                        api_key=active_key
                    )

                    analyst = Agent(
                        role="Financial Market Analyst",
                        goal="Analyze cryptocurrency market trends and provide clear trading signals",
                        backstory="You are an experienced crypto trader. You analyze markets and give clear signals.",
                        llm=custom_llm,
                        verbose=True
                    )

                    task = Task(
                        description="""Проанализируй текущую ситуацию на рынке Bitcoin (BTC).
                        Учти: сейчас май 2026 года.
                        Дай чёткую рекомендацию: КУПИТЬ / ПРОДАТЬ / ДЕРЖАТЬ.
                        Объясни своё решение в 3-4 предложениях.
                        ВАЖНО: Ответ должен быть полностью на РУССКОМ языке.""",
                        expected_output="Trading signal with justification in Russian language",
                        agent=analyst
                    )
