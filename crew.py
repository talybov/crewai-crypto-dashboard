import os
from crewai import Agent, Task, Crew, Process
from langchain.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI

# Инициализируем инструменты поиска
search_tool = DuckDuckGoSearchRun()

# Используем GPT-4o-mini (дешевле и быстрее для таких задач)
# Если хочешь другую модель, замени здесь
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY")  # Обязательно добавь в Secrets Streamlit!
)

def create_polymarket_crew(market_question, market_description, resolution_source):
    """
    Создает рой агентов для анализа конкретного рынка Polymarket
    """
    
    # === АГЕНТ 1: Market Scanner ===
    scanner = Agent(
        role="Market Scanner",
        goal="Анализировать текущие котировки и ликвидность рынка",
        backstory="""Ты эксперт по рынкам предсказаний. Твоя задача - оценить, 
        насколько текущая цена отражает реальную вероятность события. 
        Ищешь неэффективности и аномалии в объемах торгов.""",
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    # === АГЕНТ 2: News Analyst ===
    news_analyst = Agent(
        role="News & Sentiment Analyst",
        goal="Найти свежие новости и оценить их влияние на вероятность события",
        backstory="""Ты опытный аналитик новостей. Используя поиск в интернете, 
        ты находишь самые свежие и релевантные новости по теме рынка. 
        Оцениваешь, как они влияют на вероятность события.""",
        tools=[search_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    # === АГЕНТ 3: Resolution Lawyer ===
    lawyer = Agent(
        role="Resolution Source Lawyer",
        goal="Проанализировать правила резолюции и найти потенциальные риски",
        backstory="""Ты юрист, специализирующийся на контрактах и правилах. 
        Твоя задача - внимательно прочитать источник резолюции и найти 
        любые нюансы, которые могут привести к неожиданному результату.""",
        backstory_extra=f"""
        Источник резолюции для этого рынка: {resolution_source}
        """,
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    # === АГЕНТ 4: Strategy Lead ===
    strategist = Agent(
        role="Chief Strategy Officer",
        goal="Синтезировать информацию от всех агентов и выдать финальную рекомендацию",
        backstory="""Ты главный стратег хедж-фонда. Ты получаешь отчеты от аналитиков, 
        юристов и сканеров рынка. Твоя задача - рассчитать Expected Value (EV) 
        и выдать четкую рекомендацию: BUY YES, BUY NO или IGNORE.""",
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=True  # Может делегировать задачи другим агентам
    )
    
    # === ЗАДАЧИ ===
    
    # Задача 1: Анализ рынка
    scan_task = Task(
        description=f"""
        Проанализируй рынок Polymarket:
        Вопрос: {market_question}
        Описание: {market_description}
        
        Оцени:
        1. Насколько ликвиден рынок
        2. Есть ли признаки манипуляции или необычной активности
        3. Краткий вывод о текущей цене
        """,
        expected_output="Краткий анализ рынка (3-4 предложения)",
        agent=scanner
    )
    
    # Задача 2: Поиск новостей
    news_task = Task(
        description=f"""
        Найди 3-5 самых свежих новостей по теме: {market_question}
        
        Для каждой новости укажи:
        - Заголовок и источник
        - Как она влияет на вероятность события (повышает/понижает)
        - Насколько надежен источник
        
        В конце дай общий вывод: как новости меняют вероятность?
        """,
        expected_output="Список новостей с анализом и общий вывод",
        agent=news_analyst
    )
    
    # Задача 3: Анализ правил резолюции
    legal_task = Task(
        description=f"""
        Проанализируй источник резолюции: {resolution_source}
        
        Найди потенциальные риски:
        1. Есть ли двусмысленность в формулировках?
        2. Какие условия должны быть выполнены для "Yes"?
        3. Есть ли временные ограничения или другие нюансы?
        
        Оцени вероятность того, что событие будет засчитано как "True" 
        строго по правилам, даже если фактически событие произошло.
        """,
        expected_output="Юридический анализ рисков (3-4 пункта)",
        agent=lawyer
    )
    
    # Задача 4: Финальная стратегия
    strategy_task = Task(
        description=f"""
        Получи отчеты от всех агентов и выдай финальную рекомендацию.
        
        Рынок: {market_question}
        
        Твой анализ должен включать:
        1. Краткое резюме от каждого агента (1-2 предложения)
        2. Твою оценку реальной вероятности события (в %)
        3. Расчет Expected Value (EV)
        4. Финальная рекомендация: BUY YES, BUY NO или IGNORE
        5. Уверенность в рекомендации (низкая/средняя/высокая)
        6. Ключевые риски
        
        Будь конкретен и прагматичен.
        """,
        expected_output="""
        ## Финальный отчет стратегии
        
        ### Резюме агентов:
        - Market Scanner: ...
        - News Analyst: ...
        - Resolution Lawyer: ...
        
        ### Оценка вероятности: X%
        
        ### Expected Value (EV): ...
        
        ### Рекомендация: BUY YES / BUY NO / IGNORE
        
        ### Уверенность: Низкая / Средняя / Высокая
        
        ### Ключевые риски:
        1. ...
        2. ...
        """,
        agent=strategist
    )
    
    # === СОЗДАЕМ КОМАНДУ ===
    crew = Crew(
        agents=[scanner, news_analyst, lawyer, strategist],
        tasks=[scan_task, news_task, legal_task, strategy_task],
        process=Process.sequential,  # Агенты работают последовательно
        verbose=True
    )
    
    return crew

def run_crew_analysis(market_question, market_description, resolution_source):
    """
    Запускает рой агентов и возвращает результат
    """
    crew = create_polymarket_crew(market_question, market_description, resolution_source)
    result = crew.kickoff()
    return result
