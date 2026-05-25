import os
import sys
import asyncio
import streamlit as st
from crewai import Agent, Task, Crew

# Настройка стилей страницы
st.set_page_config(page_title="Crypto AI Agents Dashboard", page_icon="📊", layout="wide")
# Отключаем телеметрию CrewAI, чтобы она не ругалась при повторных запусках кнопки
os.environ["OTEL_SDK_DISABLED"] = "true"
st.title("📊 Рой ИИ-Агентов: Финансовый Анализ Рынка")
st.subheader("Мониторинг работы и взаимодействия агентов в реальном времени")

# Форма для ввода API-ключа прямо на сайте, чтобы не светить его в коде
gemini_key = st.sidebar.text_input("Введи свой GEMINI_API_KEY:", type="password")

st.sidebar.markdown("""
### Как это работает?
При нажатии кнопки запуска, Агент-Аналитик начинает сканировать рынок. 
В процессе работы его лог мышления будет выводиться в интерактивное окно справа.
""")

# Контейнер для вывода графиков и логов
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🤖 Управление Роем")
    start_button = st.button("🚀 Запустить асинхронный анализ Биткоина", use_container_width=True)
    
    status_area = st.empty()
    result_area = st.empty()

with col2:
    st.markdown("### ⚙️ Внутренние мысли и шаги Агентов")
    log_area = st.empty()

# Кастомный класс для перехвата мыслей агентов и вывода их на экран
class StreamlitStdoutTrigger:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.text = ""
    def write(self, bytes_data):
        self.text += bytes_data
        # Очищаем текст от лишних логов, делаем вывод красивым
        clean_text = self.text.replace("Entering New CrewAgentExecutor Chain", "🤖 Агент переходит к следующему шагу...")
        self.placeholder.code(clean_text)
    def flush(self):
        pass

if start_button:
    if not gemini_key:
        st.error("❌ Сначала вставь свой API-ключ Gemini в боковое меню!")
    else:
        # Чистим старые переменные и ставим новые
        if "GOOGLE_API_KEY" in os.environ: del os.environ["GOOGLE_API_KEY"]
        os.environ["GEMINI_API_KEY"] = gemini_key

        # Инициализируем агента
        analyst = Agent(
            role="Financial Market Analyst",
            goal="Analyze market trends and provide clear trading signals",
            backstory="You are an experienced crypto trader with 10 years of experience. You analyze markets and give clear signals.",
            llm="gemini/gemini-2.0-flash",
            verbose=True
        )

        task = Task(
            description="""Проанализируй текущую ситуацию на рынке Bitcoin (BTC).
            Учти: сейчас май 2026 года.
            Дай чёткую рекомендацию: КУПИТЬ / ПРОДАТЬ / ДЕРЖАТЬ.
            Объясни своё решение в 3-4 предложениях. 
            ВАЖНО: Напиши весь свой финальный ответ полностью на РУССКОМ языке.""",
            expected_output="Trading signal with justification in Russian language",
            agent=analyst
        )

        crew = Crew(agents=[analyst], tasks=[task], verbose=True)

        # Перенаправляем лог терминала CrewAI в интерфейс Streamlit
        sys.stdout = StreamlitStdoutTrigger(log_area)

        status_area.info("⏳ Агенты просыпаются и начинают обсуждение ситуации...")
        
        # Запускаем асинхронно
        try:
            result = asyncio.run(crew.kickoff_async())
            status_area.success("✅ Анализ успешно завершен!")
            
            with result_area:
                st.markdown("---")
                st.markdown("### 📊 ФИНАЛЬНЫЙ ВЕРДИКТ:")
                st.success(result)
        except Exception as e:
            status_area.error(f"❌ Произошла ошибка: {str(e)}")
        finally:
            sys.stdout = sys.__stdout__ # Возвращаем поток вывода назад
