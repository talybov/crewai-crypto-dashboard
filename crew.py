import os
from crewai import Agent, Task, Crew, Process
from langchain_community.tools import DuckDuckGoSearchRun

# Инструмент поиска
search_tool = DuckDuckGoSearchRun()

def create_polymarket_crew(market_question, market_description, resolution_source):
    """Создает рой агентов для анализа рынка Polymarket"""
    
    # === АГЕНТ 1: Сканирует рынок ===
    scanner = Agent(
        role="Market Scanner",
        goal="Анализировать текущие котировки и ликвидность рынка",
        backstory="""Ты эксперт по рынкам предсказаний. Оцениваешь, 
        насколько текущая цена отражает реальную вероятность события.""",
        verbose=True,
        allow_delegation=False,
        llm="gpt-4o-mini"  # В 0.11.2 llm передается как СТРОКА
    )
    
    # === АГЕНТ 2: Анализирует новости ===
    news_analyst = Agent(
        role="News Analyst",
        goal="Найти свежие новости и оценить их влияние",
        backstory="""Ты аналитик новостей. Ищешь свежие новости 
        по теме рынка и оцениваешь их влияние.""",
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
        llm="gpt-4o-mini"
    )
    
    # === АГЕНТ 3: Юрист по резолюциям ===
    lawyer = Agent(
        role="Resolution Lawyer",
        goal="Проанализировать правила резолюции и найти риски",
        backstory="""Ты юрист. Твоя задача - найти нюансы в правилах 
        резолюции, которые могут повлиять на результат.""",
        verbose=True,
        allow_delegation=False,
        llm="gpt-4o-mini"
    )
    
    # === АГЕНТ 4: Главный стратег ===
    strategist = Agent(
        role="Strategy Officer",
        goal="Синтезировать отчеты и дать рекомендацию",
        backstory="""Ты главный стратег. Собираешь отчеты от всех 
        агентов и выдаешь финальную рекомендацию: BUY YES, BUY NO или IGNORE.""",
        verbose=True,
        allow_delegation=True,
        llm="gpt-4o-mini"
    )
    
    # === ЗАДАЧИ ===
    scan_task = Task(
        description=f"""Проанализируй рынок Polymarket:
        Вопрос: {market_question}
        Описание: {market_description}
        Оцени ликвидность и текущую цену.""",
        expected_output="Краткий анализ рынка (3-4 предложения)",
        agent=scanner
    )
    
    news_task = Task(
        description=f"""Найди 3-5 свежих новостей по теме: 
        {market_question}. Для каждой укажи источник и влияние 
        на вероятность события.""",
        expected_output="Список новостей с анализом и общий вывод",
        agent=news_analyst
    )
    
    legal_task = Task(
        description=f"""Проанализируй источник резолюции: 
        {resolution_source}. Найди риски и двусмысленности 
        в формулировках.""",
        expected_output="Юридический анализ рисков (3-4 пункта)",
        agent=lawyer
    )
    
    strategy_task = Task(
        description=f"""Собери отчеты от всех агентов по рынку: 
        {market_question}. Выдай финальную рекомендацию с оценкой 
        вероятности, Expected Value и уверенностью.""",
        expected_output="""
        ### Резюме агентов:
        - Market Scanner: ...
        - News Analyst: ...
        - Resolution Lawyer: ...
        
        ### Оценка вероятности: X%
        ### Рекомендация: BUY YES / BUY NO / IGNORE
        ### Уверенность: Низкая / Средняя / Высокая
        ### Ключевые риски: ...
        """,
        agent=strategist
    )
    
    # === СОБИРАЕМ КОМАНДУ ===
    crew = Crew(
        agents=[scanner, news_analyst, lawyer, strategist],
        tasks=[scan_task, news_task, legal_task, strategy_task],
        verbose=True,
        process=Process.sequential
    )
    
    return crew

def run_crew_analysis(market_question, market_description, resolution_source):
    """Запускает рой и возвращает результат"""
    crew = create_polymarket_crew(market_question, market_description, resolution_source)
    result = crew.kickoff()
    return result
