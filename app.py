import os
import sys
import streamlit as st

# 1. Отключаем проблемный трекер OpenTelemetry до импорта CrewAI
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

# 2. Настройка стилей страницы Streamlit
st.set_page_config(page_title="Crypto AI Agents Dashboard", page_icon="📊", layout="wide")

st.title("📊 Рой ИИ-Агентов: Финансовый Анализ Рынка")
st.subheader("Мониторинг работы и взаимодействия агентов в реальном времени")

# 3. Боковое меню для ввода ключа
gemini_key = st.sidebar.text_input("Введи свой GEMINI_API_KEY:", type="password")

st.sidebar.markdown("""
### Как это работает?
При нажатии кнопки запуска, Агент-Аналитик начинает сканировать рынок. 
В процессе работы его лог мышления будет выводиться в интерактивное окно справа.
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

# 4. Класс для перехвата логов из терминала и вывода их на экран Streamlit
class StreamlitStdoutTrigger:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.text = ""
    def write(self, bytes_data):
        self.text += bytes_data
        # Делаем вывод системных логов более читаемым
        clean_text = self.text.replace("Entering New CrewAgentExecutor Chain", "🤖 Агент переходит к следующему шагу...")
        self.placeholder.code(clean_text)
    def flush(self):
        pass

# 5. Логика работы при нажатии на кнопку
if start_button:
    if not gemini_key:
        st.error("❌ Сначала вставь свой API-ключ Gemini в боковое меню!")
    else:
        # Устанавливаем ключ в переменную среды
        os.environ["GEMINI_API_KEY"] = gemini_key

        status_area.info("⏳ Агент просыпается и начинает анализ рынка...")

        try:
            # Настраиваем модель через официальный объект LLM, чтобы избежать капризов litellm
            custom_llm = LLM(
                model="gemini/gemini-2.0-flash",
                api_key=gemini_key
            )

            # Инициализируем агента и передаем ему объект модели
            analyst = Agent(
                role="Financial Market Analyst",
                goal="Analyze cryptocurrency market trends and provide clear trading signals",
                backstory="You are an experienced crypto trader. You analyze markets and give clear signals.",
                llm=custom_llm,
                verbose=True
            )

            # Формируем задачу
            task = Task(
                description="""Проанализируй текущую ситуацию на рынке Bitcoin (BTC).
                Учти: сейчас май 2026 года.
                Дай чёткую рекомендацию: КУПИТЬ / ПРОДАТЬ / ДЕРЖАТЬ.
                Объясни своё решение в 3-4 предложениях.
                ВАЖНО: Ответ должен быть полностью на РУССКОМ языке.""",
                expected_output="Trading signal with justification in Russian language",
                agent=analyst
            )

            # Собираем команду
            crew = Crew(agents=[analyst], tasks=[task], verbose=True)

            # Перенаправляем стандартный вывод терминала в наше правое окно на сайте
            old_stdout = sys.stdout
            sys.stdout = StreamlitStdoutTrigger(log_area)
            
            # Запускаем синхронный процесс
            result = crew.kickoff()
            
            # Возвращаем стандартный вывод назад системе
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
