import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
import time
import os  # <-- ДОБАВЛЕНО: для проверки API ключа
from agent_state import update_agent_status, get_all_states
from crew import run_crew_analysis  # <-- ДОБАВЛЕНО: импорт функции роя

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ
st.set_page_config(page_title="Polymarket AI Swarm", layout="wide")

# 2. ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ
@st.cache_data(ttl=300)
def get_polymarket_markets():
    """Получаем топ рынки Polymarket по объему за 24 часа"""
    url = "https://gamma-api.polymarket.com/markets"
    params = {"closed": "false", "limit": 15, "order": "volume24hr", "ascending": "false"}
    try:
        return requests.get(url, params=params).json()
    except Exception as e:
        st.error(f"Ошибка API: {e}")
        return []

# 3. ИНТЕРФЕЙС ДАШБОРДА
st.title("🦇 Polymarket AI Swarm Dashboard")

# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("🏢 Операционный штаб")
    
    states = get_all_states()
    if not states:
        st.info("Агенты спят. Запустите анализ!")
    else:
        for agent, info in states.items():
            icon = "🟢" if info['status'] == 'Активен' else "⚪"
            st.markdown(f"**{icon} {agent}**")
            st.caption(f"_{info['task']}_")
            st.divider()
            
    st.markdown("---")
    
    markets = get_polymarket_markets()
    if not markets:
        st.stop()
        
    market_options = {m['question']: m for m in markets}
    selected_q = st.selectbox("Выберите рынок для анализа", list(market_options.keys()))
    selected_market = market_options[selected_q]
    
    run_btn = st.button("🚀 Запустить Рой Агентов", type="primary", use_container_width=True)

# --- ОСНОВНАЯ ОБЛАСТЬ ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📊 {selected_q}")
    
    try:
        prices = eval(selected_market.get('outcomePrices', '[]'))
        yes_price = float(prices[0]) * 100 if prices else 50.0
    except:
        yes_price = 50.0
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pd.date_range(end=datetime.now(), periods=24, freq='h'), # 'h' строчная!
        y=[yes_price + i*0.2 - 2 for i in range(24)], 
        mode='lines+markers',
        name='Вероятность YES (%)',
        line=dict(color='#00FFFF', width=3)
    ))
    fig.update_layout(
        template="plotly_dark", 
        height=400, 
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Текущая цена YES", f"{yes_price:.1f}%")
    m2.metric("Объем 24ч", f"${float(selected_market.get('volume24hr', 0)):,.0f}")
    m3.metric("Ликвидность", f"${float(selected_market.get('liquidity', 0)):,.0f}")

with col2:
    st.subheader("📋 Логи работы роя")
    
    if run_btn:
        # ПРОВЕРКА API КЛЮЧА
        if not os.getenv("OPENAI_API_KEY"):
            st.error("❌ Не найден OPENAI_API_KEY!")
            st.info("Добавь его в Secrets: Manage app → Secrets → `OPENAI_API_KEY = 'sk-...'`")
        else:
            with st.status("🤖 Рой агентов анализирует рынок...", expanded=True) as status:
                try:
                    question = selected_market.get('question', '')
                    description = selected_market.get('description', '')
                    resolution = selected_market.get('resolution_source', 'Не указан')
                    
                    st.write("🔍 Запускаем агентов (это займет 10-20 секунд)...")
                    
                    # ЗАПУСК РЕАЛЬНОГО РОЯ
                    result = run_crew_analysis(question, description, resolution)
                    
                    st.write("✅ Анализ завершен!")
                    status.update(label="Анализ завершен!", state="complete", expanded=False)
                    
                    st.markdown("---")
                    st.markdown("### 🎯 Результат анализа:")
                    st.markdown(result)
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Ошибка при запуске роя: {e}")
                    st.info("Проверь логи в 'Manage app' для деталей.")
    else:
        st.info("Выберите рынок слева и нажмите 'Запустить Рой'.")
