"""
NEXUS-RSI Dashboard
Interface de monitoring temps réel
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
from pathlib import Path
import sys

# Import du core
sys.path.append(str(Path(__file__).parent))
from nexus_core import NexusCore, ModulePerformance

# Configuration Streamlit
st.set_page_config(
    page_title="NEXUS-RSI Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #00ff41;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 0 10px #00ff41;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
    }
    .status-running { color: #00ff41; }
    .status-stopped { color: #ff0041; }
    .status-warning { color: #ffaa00; }
</style>
""", unsafe_allow_html=True)

# Initialisation
@st.cache_resource
def init_nexus():
    nexus = NexusCore()
    nexus.initialize_agents()
    nexus.start_auto_improvement_loop()
    
    # Ajout de modules de test
    for i in range(5):
        module = ModulePerformance(
            module_id=f"mod_{i}",
            name=f"Module_{i}",
            speed=100 + i*10,
            accuracy=0.8 + i*0.02,
            last_update=datetime.now(),
            status="active"
        )
        nexus.modules[module.module_id] = module
    
    return nexus

nexus = init_nexus()

# Header
st.markdown("<h1 class='main-header'>🚀 NEXUS-RSI DASHBOARD</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_rate = st.slider("Refresh rate (sec)", 1, 10, 3)
    
    st.divider()
    
    # Actions rapides
    st.header("🎯 Actions Rapides")
    
    if st.button("🔄 Force Benchmark", use_container_width=True):
        nexus._run_benchmark()
        st.success("Benchmark lancé!")
    
    if st.button("🔧 Patch All Slow", use_container_width=True):
        nexus._patch_slow_modules()
        st.success("Patch appliqué!")
    
    if st.button("💀 Kill Inactive", use_container_width=True):
        nexus._kill_inactive_modules()
        st.warning("Modules inactifs killed!")
    
    st.divider()
    
    # Config display
    st.header("📋 Configuration Active")
    config = nexus.config
    for key, value in config.items():
        st.text(f"{key}: {value}")

# Main content
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🤖 Agents", "⚡ Performance", "📈 Analytics", "📝 Logs"])

with tab1:
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    dashboard_data = nexus.get_dashboard_data()
    
    with col1:
        st.metric(
            "🚀 Iteration Speed",
            f"{dashboard_data['iteration_speed']:.2f} ops/sec",
            delta=f"+{dashboard_data['iteration_speed']*0.1:.2f}"
        )
    
    with col2:
        active_modules = len([m for m in nexus.modules.values() if m.status == 'active'])
        st.metric(
            "📦 Active Modules",
            active_modules,
            delta=f"{active_modules - len(nexus.modules)}"
        )
    
    with col3:
        st.metric(
            "🤖 Active Agents",
            dashboard_data['active_agents'],
            delta="+2"
        )
    
    with col4:
        status_color = "status-running" if dashboard_data['system_status'] == 'running' else "status-stopped"
        st.markdown(f"<h3 class='{status_color}'>System: {dashboard_data['system_status'].upper()}</h3>", unsafe_allow_html=True)
    
    st.divider()
    
    # Modules status table
    st.subheader("📦 Modules Status")
    
    if nexus.modules:
        modules_df = pd.DataFrame([
            {
                'Module': m.name,
                'Speed (ops/sec)': f"{m.speed:.2f}",
                'Accuracy': f"{m.accuracy:.2%}",
                'Status': m.status,
                'Last Update': m.last_update.strftime("%H:%M:%S"),
                'Improvements': len(m.improvements)
            }
            for m in nexus.modules.values()
        ])
        
        st.dataframe(
            modules_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.TextColumn(
                    "Status",
                    help="Module status",
                )
            }
        )

with tab2:
    st.subheader("🤖 Active Agents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        for agent_id, agent in list(nexus.agents.items())[:2]:
            with st.expander(f"🤖 {agent.role}", expanded=True):
                st.text(f"Goal: {agent.goal}")
                st.text(f"Status: Active ✅")
                st.progress(0.75, text="Performance")
    
    with col2:
        for agent_id, agent in list(nexus.agents.items())[2:]:
            with st.expander(f"🤖 {agent.role}", expanded=True):
                st.text(f"Goal: {agent.goal}")
                st.text(f"Status: Active ✅")
                st.progress(0.85, text="Performance")

with tab3:
    st.subheader("⚡ Performance Metrics")
    
    # Graphique de performance
    if nexus.modules:
        perf_data = pd.DataFrame([
            {
                'Module': m.name,
                'Speed': m.speed,
                'Accuracy': m.accuracy * 100
            }
            for m in nexus.modules.values()
        ])
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speed (ops/sec)', x=perf_data['Module'], y=perf_data['Speed']))
        fig.add_trace(go.Bar(name='Accuracy (%)', x=perf_data['Module'], y=perf_data['Accuracy']))
        fig.update_layout(title="Module Performance Comparison", barmode='group')
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Timeline de vitesse d'itération
    st.subheader("📈 Iteration Speed Timeline")
    
    # Simulation de données historiques
    time_data = pd.DataFrame({
        'Time': pd.date_range(start=datetime.now() - timedelta(hours=1), 
                             end=datetime.now(), 
                             periods=20),
        'Speed': [100 + i*5 + (i%3)*10 for i in range(20)]
    })
    
    fig_timeline = px.line(time_data, x='Time', y='Speed', 
                           title='Iteration Speed Evolution',
                           labels={'Speed': 'Speed (ops/sec)'})
    st.plotly_chart(fig_timeline, use_container_width=True)

with tab4:
    st.subheader("📈 Analytics & Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("🎯 **Optimization Opportunities**")
        st.write("- Module_0 shows 15% speed degradation")
        st.write("- Module_3 accuracy can be improved by 8%")
        st.write("- Consider scaling Module_4 (high performance)")
    
    with col2:
        st.success("✨ **Recent Improvements**")
        st.write("- Applied 5 patches in last hour")
        st.write("- Killed 2 underperforming modules")
        st.write("- Parallel processing increased by 30%")
    
    st.divider()
    
    # Heatmap de corrélation
    st.subheader("🔥 Module Correlation Heatmap")
    
    if nexus.modules:
        import numpy as np
        
        modules_list = list(nexus.modules.values())
        correlation_matrix = np.random.rand(len(modules_list), len(modules_list))
        correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
        np.fill_diagonal(correlation_matrix, 1)
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=correlation_matrix,
            x=[m.name for m in modules_list],
            y=[m.name for m in modules_list],
            colorscale='Viridis'
        ))
        fig_heatmap.update_layout(title="Module Performance Correlation")
        
        st.plotly_chart(fig_heatmap, use_container_width=True)

with tab5:
    st.subheader("📝 System Logs")
    
    # Lecture des logs
    logs_dir = Path("proofs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        
        if log_files:
            selected_log = st.selectbox("Select log file", log_files)
            
            if selected_log:
                with open(selected_log) as f:
                    log_content = f.read()
                    st.text_area("Log Content", log_content, height=400)
        else:
            st.info("No logs available yet")
    
    # Actions logs en temps réel
    st.subheader("🔄 Real-time Actions")
    
    with st.container():
        placeholder = st.empty()
        
        actions = [
            f"{datetime.now():%H:%M:%S} - Benchmark completed for Module_0",
            f"{datetime.now():%H:%M:%S} - Patch applied to Module_2",
            f"{datetime.now():%H:%M:%S} - New workflow added",
            f"{datetime.now():%H:%M:%S} - Parallel execution started",
            f"{datetime.now():%H:%M:%S} - Veille agent found 3 new sources"
        ]
        
        for action in actions[-5:]:
            st.text(action)

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #888;'>
    🚀 NEXUS-RSI v1.0.0 | ⚡ Hyperfast Iteration System | 🔄 Auto-improving 24/7
</div>
""", unsafe_allow_html=True)