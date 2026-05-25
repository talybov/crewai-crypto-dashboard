import os
import sys
import streamlit as st

# 1. Отключаем проблемный трекер OpenTelemetry до импорта CrewAI
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

# 2. Настройка стилей страницы Streamlit
st.set_page_config(page_title="Multi-Key Crypto AI Dashboard", page_icon="📊", layout="wide")

st.title("📊 Рой ИИ-Агентов с ротацией API-ключей")
st.subheader("Система обхода лимитов для бесплатного тарифа Gemini")

# 3. Боковое меню для ввода НЕСКОЛЬКИХ ключей
st.sidebar.markdown("### 🔑 Пул API-ключей Gemini")
keys_input = st.sidebar.text_area(
    "Вставь сюда свои API-ключи (каждый ключ с новой строки):", 
    height=150, 
    type="password",
    placeholder="AIzaSy...\nAIzaSy...\nAIzaSy..."
)

st.sidebar.markdown("""
### 💡 Как это работает?
Выпусти 2-3 бесплатных ключа на разные Google-аккаунты и вставь их сюда. 
Программа создаст из них очередь. Если один ключ упрется в лимит запросов, система автоматически переключится на следующий!
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
        def run_crew_with_retry(max_attempts=3):
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

                    crew = Crew(agents=[analyst], tasks=[task], verbose=True)
                    return crew.kickoff()

                except Exception as e:
                    error_msg = str(e)
                    # Если поймали лимит квот (429) и у нас есть другие ключи — ротируем!
                    if ("429" in error_msg or "Quota exceeded" in error_msg) and rotator.rotate():
                        st.warning(f"⚠️ Ключ №{rotator.index} исчерпал лимиты. Автоматически переключаюсь на ключ №{rotator.index + 1}...")
                        continue
                    else:
                        raise e # Если ключи кончились или ошибка другая — пробрасываем дальше

        # Перенаправляем лог терминала на сайт
        old_stdout = sys.stdout
        sys.stdout = StreamlitStdoutTrigger(log_area)
        
        try:
            # Запускаем нашу умную функцию с защитой от блокировок
            result = run_crew_with_retry(max_attempts=len(rotator.keys) + 1)
            
            sys.stdout = old_stdout
            status_area.success("✅ Анализ успешно завершен!")
            with result_area:
                st.markdown("---")
                st.markdown("### 📊 ФИНАЛЬНЫЙ ВЕРДИКТ:")
                st.success(str(result))
                
        except Exception as e:
            if 'old_stdout' in locals() and sys.stdout != old_stdout:
                sys.stdout = old_stdout
            status_area.error(f"❌ Произошла ошибка: {str(e)}")
