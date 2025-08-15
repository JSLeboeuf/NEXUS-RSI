#!/usr/bin/env python3
"""
NEXUS-RSI Wave Dashboard
Real-time monitoring and visualization of wave orchestration
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import json
import time
from pathlib import Path
import asyncio
from typing import Dict, List, Any

# Page configuration
st.set_page_config(
    page_title="NEXUS-RSI Wave Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class WaveDashboard:
    """Wave monitoring dashboard"""
    
    def __init__(self):
        self.db_path = Path("nexus_waves.db")
        self.init_session_state()
        
    def init_session_state(self):
        """Initialize session state variables"""
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 5
        if 'selected_wave' not in st.session_state:
            st.session_state.selected_wave = None
            
    def get_wave_data(self) -> pd.DataFrame:
        """Fetch wave data from database"""
        if not self.db_path.exists():
            return pd.DataFrame()
            
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT wave_id, strategy, complexity_score, file_count, 
                   start_time, end_time, status, phases_completed, total_phases
            FROM waves
            ORDER BY start_time DESC
            LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert timestamps
        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'], unit='s')
            df['end_time'] = pd.to_datetime(df['end_time'], unit='s')
            df['duration'] = (df['end_time'] - df['start_time']).dt.total_seconds()
            
        return df
        
    def get_phase_data(self, wave_id: str) -> pd.DataFrame:
        """Fetch phase data for a specific wave"""
        if not self.db_path.exists():
            return pd.DataFrame()
            
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT phase, start_time, end_time, status, agent_primary, agents_support
            FROM wave_phases
            WHERE wave_id = ?
            ORDER BY start_time
        """
        df = pd.read_sql_query(query, conn, params=(wave_id,))
        conn.close()
        
        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'], unit='s')
            df['end_time'] = pd.to_datetime(df['end_time'], unit='s')
            df['duration'] = (df['end_time'] - df['start_time']).dt.total_seconds()
            
        return df
        
    def render_wave_overview(self):
        """Render wave overview section"""
        st.header("🌊 Wave Orchestration Overview")
        
        waves_df = self.get_wave_data()
        
        if waves_df.empty:
            st.info("No wave executions found. Start a wave to see data here.")
            return
            
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_waves = len(waves_df)
            st.metric("Total Waves", total_waves)
            
        with col2:
            success_rate = (waves_df['status'] == 'completed').mean() * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
            
        with col3:
            avg_complexity = waves_df['complexity_score'].mean()
            st.metric("Avg Complexity", f"{avg_complexity:.2f}")
            
        with col4:
            avg_duration = waves_df['duration'].mean()
            st.metric("Avg Duration", f"{avg_duration:.1f}s" if not pd.isna(avg_duration) else "N/A")
            
        # Wave timeline
        st.subheader("Wave Execution Timeline")
        
        fig = go.Figure()
        
        for _, wave in waves_df.iterrows():
            color = 'green' if wave['status'] == 'completed' else 'orange' if wave['status'] == 'partial' else 'red'
            
            fig.add_trace(go.Scatter(
                x=[wave['start_time'], wave['end_time'] if pd.notna(wave['end_time']) else datetime.now()],
                y=[wave['wave_id'], wave['wave_id']],
                mode='lines+markers',
                name=wave['wave_id'],
                line=dict(color=color, width=4),
                marker=dict(size=8),
                hovertemplate=f"Wave: {wave['wave_id']}<br>Strategy: {wave['strategy']}<br>Status: {wave['status']}"
            ))
            
        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_title="Time",
            yaxis_title="Wave ID",
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def render_strategy_analysis(self):
        """Render strategy analysis section"""
        st.header("📊 Strategy Analysis")
        
        waves_df = self.get_wave_data()
        
        if waves_df.empty:
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            # Strategy distribution
            strategy_counts = waves_df['strategy'].value_counts()
            
            fig = px.pie(
                values=strategy_counts.values,
                names=strategy_counts.index,
                title="Strategy Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Success rate by strategy
            strategy_success = waves_df.groupby('strategy').apply(
                lambda x: (x['status'] == 'completed').mean() * 100
            )
            
            fig = px.bar(
                x=strategy_success.index,
                y=strategy_success.values,
                title="Success Rate by Strategy",
                labels={'x': 'Strategy', 'y': 'Success Rate (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
    def render_wave_details(self):
        """Render detailed wave information"""
        st.header("🔍 Wave Details")
        
        waves_df = self.get_wave_data()
        
        if waves_df.empty:
            return
            
        # Wave selector
        wave_ids = waves_df['wave_id'].tolist()
        selected_wave = st.selectbox("Select Wave", wave_ids)
        
        if selected_wave:
            wave_info = waves_df[waves_df['wave_id'] == selected_wave].iloc[0]
            
            # Wave info
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Strategy", wave_info['strategy'])
                st.metric("Complexity", f"{wave_info['complexity_score']:.2f}")
                
            with col2:
                st.metric("File Count", wave_info['file_count'])
                st.metric("Status", wave_info['status'])
                
            with col3:
                st.metric("Phases", f"{wave_info['phases_completed']}/{wave_info['total_phases']}")
                duration = wave_info['duration'] if pd.notna(wave_info['duration']) else 0
                st.metric("Duration", f"{duration:.1f}s")
                
            # Phase breakdown
            st.subheader("Phase Execution")
            
            phases_df = self.get_phase_data(selected_wave)
            
            if not phases_df.empty:
                # Gantt chart for phases
                fig = go.Figure()
                
                for i, phase in phases_df.iterrows():
                    color = 'green' if phase['status'] == 'completed' else 'red'
                    
                    fig.add_trace(go.Scatter(
                        x=[phase['start_time'], phase['end_time'] if pd.notna(phase['end_time']) else datetime.now()],
                        y=[phase['phase'], phase['phase']],
                        mode='lines',
                        line=dict(color=color, width=20),
                        name=phase['phase'],
                        hovertemplate=f"Phase: {phase['phase']}<br>Duration: {phase['duration']:.1f}s<br>Agent: {phase['agent_primary']}"
                    ))
                    
                fig.update_layout(
                    height=300,
                    showlegend=False,
                    xaxis_title="Time",
                    yaxis_title="Phase",
                    hovermode='closest'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Phase table
                st.dataframe(
                    phases_df[['phase', 'status', 'agent_primary', 'duration']],
                    use_container_width=True
                )
                
    def render_live_monitoring(self):
        """Render live monitoring section"""
        st.header("⚡ Live Monitoring")
        
        # Auto-refresh settings
        col1, col2 = st.columns([3, 1])
        
        with col2:
            refresh = st.checkbox("Auto-refresh", value=True)
            if refresh:
                interval = st.slider("Refresh interval (s)", 1, 30, 5)
                st.session_state.refresh_interval = interval
                
        # Get latest waves
        waves_df = self.get_wave_data()
        
        if not waves_df.empty:
            # Active waves
            active_waves = waves_df[waves_df['status'] == 'in_progress']
            
            if not active_waves.empty:
                st.subheader("🔄 Active Waves")
                
                for _, wave in active_waves.iterrows():
                    progress = wave['phases_completed'] / wave['total_phases'] if wave['total_phases'] > 0 else 0
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.progress(progress)
                        st.caption(f"Wave {wave['wave_id']} - {wave['strategy']} - Phase {wave['phases_completed']}/{wave['total_phases']}")
                        
                    with col2:
                        elapsed = (datetime.now() - wave['start_time']).total_seconds()
                        st.metric("Elapsed", f"{elapsed:.0f}s")
                        
            # Recent completions
            st.subheader("✅ Recent Completions")
            
            recent = waves_df[waves_df['status'].isin(['completed', 'partial'])].head(5)
            
            if not recent.empty:
                for _, wave in recent.iterrows():
                    status_icon = "✅" if wave['status'] == 'completed' else "⚠️"
                    st.write(f"{status_icon} **{wave['wave_id']}** - {wave['strategy']} - {wave['duration']:.1f}s")
                    
        # Auto-refresh
        if refresh:
            time.sleep(st.session_state.refresh_interval)
            st.rerun()
            
    def render_sidebar(self):
        """Render sidebar controls"""
        with st.sidebar:
            st.title("🌊 Wave Control")
            
            st.subheader("Quick Actions")
            
            if st.button("🚀 Start New Wave"):
                st.info("Wave initiated (simulated)")
                
            if st.button("🛑 Stop All Waves"):
                st.warning("All waves stopped (simulated)")
                
            st.divider()
            
            st.subheader("Wave Strategies")
            st.write("**Progressive**: Iterative enhancement")
            st.write("**Systematic**: Methodical analysis")
            st.write("**Adaptive**: Dynamic configuration")
            st.write("**Enterprise**: Large-scale orchestration")
            
            st.divider()
            
            st.subheader("System Status")
            
            # Check if orchestrator is running
            orchestrator_status = "🟢 Running" if Path("nexus_orchestrator.db").exists() else "🔴 Stopped"
            st.metric("Orchestrator", orchestrator_status)
            
            # Check agent status
            agent_db = Path("nexus_metrics.db")
            if agent_db.exists():
                conn = sqlite3.connect(agent_db)
                try:
                    # This is a placeholder query - adjust based on actual schema
                    cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    table_count = cursor.fetchone()[0]
                    st.metric("Agent Tables", table_count)
                except:
                    st.metric("Agents", "N/A")
                finally:
                    conn.close()
                    
    def run(self):
        """Run the dashboard"""
        st.title("🌊 NEXUS-RSI Wave Dashboard")
        st.caption("Multi-Stage Orchestration with Compound Intelligence")
        
        # Sidebar
        self.render_sidebar()
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Strategy Analysis", "Wave Details", "Live Monitoring"])
        
        with tab1:
            self.render_wave_overview()
            
        with tab2:
            self.render_strategy_analysis()
            
        with tab3:
            self.render_wave_details()
            
        with tab4:
            self.render_live_monitoring()

def main():
    """Main entry point"""
    dashboard = WaveDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()