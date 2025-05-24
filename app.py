"""
SEO Striking Distance Analyzer - Enhanced Version
An improved tool for finding keyword optimization opportunities
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import requests
import json
from datetime import datetime
import io
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import custom modules
from utils import DataProcessor, KeywordAnalyzer, APIClient
from visualizations import create_opportunity_chart, create_keyword_distribution

# Page configuration
st.set_page_config(
    page_title="SEO Striking Distance Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'settings' not in st.session_state:
    st.session_state.settings = {
        'min_volume': 10,
        'min_position': 4,
        'max_position': 20,
        'drop_all_true': True,
        'pagination_filters': 'filterby|page|p=',
        'api_enabled': False
    }

def main():
    st.title("🎯 SEO Striking Distance Analyzer")
    st.markdown("### Find and optimize your best keyword opportunities")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Position range settings
        st.subheader("Position Range")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.settings['min_position'] = st.number_input(
                "Min Position", 
                min_value=1, 
                max_value=50, 
                value=st.session_state.settings['min_position']
            )
        with col2:
            st.session_state.settings['max_position'] = st.number_input(
                "Max Position", 
                min_value=1, 
                max_value=100, 
                value=st.session_state.settings['max_position']
            )
        
        # Volume settings
        st.session_state.settings['min_volume'] = st.number_input(
            "Minimum Search Volume", 
            min_value=0, 
            value=st.session_state.settings['min_volume']
        )
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            st.session_state.settings['drop_all_true'] = st.checkbox(
                "Drop keywords already optimized", 
                value=st.session_state.settings['drop_all_true']
            )
            st.session_state.settings['pagination_filters'] = st.text_input(
                "Pagination filters (pipe-separated)", 
                value=st.session_state.settings['pagination_filters']
            )
        
        # API Configuration
        st.subheader("🔌 API Configuration")
        use_api = st.checkbox("Enable API for keyword metrics")
        
        if use_api:
            st.info("📊 DataForSEO provides real-time search volumes, competition metrics, and CPC data.")
            
            col1, col2 = st.columns(2)
            with col1:
                api_email = st.text_input("DataForSEO Email", type="password")
            with col2:
                api_key = st.text_input("DataForSEO API Key", type="password")
            
            if api_email and api_key:
                if st.button("Test Connection"):
                    with st.spinner("Testing API connection..."):
                        api_client = APIClient(api_email, api_key)
                        if api_client.test_connection():
                            st.success("✅ API connection successful!")
                            st.session_state.api_client = api_client
                            st.session_state.settings['api_enabled'] = True
                        else:
                            st.error("❌ API connection failed. Please check credentials.")
            else:
                st.info("Enter your DataForSEO credentials to enable real-time keyword metrics")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📊 Analysis", "📈 Visualizations", "📚 Help"])
    
    with tab1:
        run_analysis()
    
    with tab2:
        show_visualizations()
    
    with tab3:
        show_help()

def run_analysis():
    st.header("Upload Your Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ Keyword Export")
        keyword_file = st.file_uploader(
            "Upload keyword ranking data (CSV)",
            type=['csv'],
            help="Export from Ahrefs, SEMrush, or similar tool"
        )
    
    with col2:
        st.subheader("2️⃣ Website Crawl")
        crawl_file = st.file_uploader(
            "Upload website crawl data (CSV)",
            type=['csv'],
            help="Export from Screaming Frog or similar crawler"
        )
    
    if keyword_file and crawl_file:
        if st.button("🚀 Run Analysis", type="primary"):
            with st.spinner("Processing data..."):
                try:
                    # Initialize processor
                    processor = DataProcessor(st.session_state.settings)
                    
                    # Process files
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Step 1: Load keyword data
                    status_text.text("Loading keyword data...")
                    df_keywords = processor.load_keyword_data(keyword_file)
                    progress_bar.progress(0.2)
                    
                    # Step 2: Load crawl data
                    status_text.text("Loading crawl data...")
                    df_crawl = processor.load_crawl_data(crawl_file)
                    progress_bar.progress(0.4)
                    
                    # Step 3: Process and analyze
                    status_text.text("Analyzing striking distance opportunities...")
                    analyzer = KeywordAnalyzer(
                        df_keywords, 
                        df_crawl, 
                        st.session_state.settings,
                        st.session_state.api_client
                    )
                    
                    results = analyzer.analyze()
                    progress_bar.progress(0.8)
                    
                    # Step 4: Enrich with API data if enabled
                    if st.session_state.settings['api_enabled'] and st.session_state.api_client:
                        status_text.text("Fetching additional keyword metrics...")
                        results = analyzer.enrich_with_api_data(results)
                    
                    progress_bar.progress(1.0)
                    status_text.text("Analysis complete!")
                    
                    # Store results
                    st.session_state.processed_data = results
                    
                    # Display results
                    display_results(results)
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.exception(e)

def display_results(results: pd.DataFrame):
    st.success(f"✅ Found {len(results)} pages with striking distance opportunities!")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_volume = results['Striking Dist. Vol'].sum()
        st.metric("Total Opportunity Volume", f"{total_volume:,}")
    
    with col2:
        total_keywords = results['KWs in Striking Dist.'].sum()
        st.metric("Total Keywords", f"{total_keywords:,}")
    
    with col3:
        avg_keywords = results['KWs in Striking Dist.'].mean()
        st.metric("Avg Keywords per Page", f"{avg_keywords:.1f}")
    
    with col4:
        if 'Avg Difficulty' in results.columns:
            avg_difficulty = results['Avg Difficulty'].mean()
            st.metric("Avg Keyword Difficulty", f"{avg_difficulty:.1f}")
    
    # Filters
    st.subheader("🔍 Filter Results")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_vol_filter = st.slider(
            "Min Total Volume",
            min_value=0,
            max_value=int(results['Striking Dist. Vol'].max()),
            value=0
        )
    
    with col2:
        min_kw_filter = st.slider(
            "Min Keywords Count",
            min_value=0,
            max_value=int(results['KWs in Striking Dist.'].max()),
            value=0
        )
    
    with col3:
        if 'Avg Difficulty' in results.columns:
            max_diff_filter = st.slider(
                "Max Avg Difficulty",
                min_value=0,
                max_value=100,
                value=100
            )
        else:
            max_diff_filter = 100
    
    # Apply filters
    filtered_results = results[
        (results['Striking Dist. Vol'] >= min_vol_filter) &
        (results['KWs in Striking Dist.'] >= min_kw_filter)
    ]
    
    if 'Avg Difficulty' in results.columns:
        filtered_results = filtered_results[filtered_results['Avg Difficulty'] <= max_diff_filter]
    
    # Display table
    st.subheader(f"📋 Results ({len(filtered_results)} pages)")
    
    # Configure display columns
    display_cols = ['URL', 'Title', 'Striking Dist. Vol', 'KWs in Striking Dist.']
    for i in range(1, 6):
        if f'KW{i}' in filtered_results.columns:
            display_cols.extend([f'KW{i}', f'KW{i} Vol'])
            if st.session_state.settings['api_enabled']:
                if f'KW{i} Difficulty' in filtered_results.columns:
                    display_cols.append(f'KW{i} Difficulty')
    
    # Show dataframe with styling
    st.dataframe(
        filtered_results[display_cols].head(50),
        use_container_width=True,
        height=400
    )
    
    # Download options
    st.subheader("💾 Export Results")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = filtered_results.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"striking_distance_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Excel download with formatting
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_results.to_excel(writer, index=False, sheet_name='Opportunities')
            
            # Add formatting
            workbook = writer.book
            worksheet = writer.sheets['Opportunities']
            
            # Format headers
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#D7E4BD',
                'border': 1
            })
            
            for col_num, value in enumerate(filtered_results.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        excel_data = output.getvalue()
        st.download_button(
            label="Download as Excel",
            data=excel_data,
            file_name=f"striking_distance_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def show_visualizations():
    if st.session_state.processed_data is None:
        st.info("Please run the analysis first to see visualizations.")
        return
    
    results = st.session_state.processed_data
    
    # Opportunity Distribution Chart
    st.subheader("📊 Opportunity Distribution")
    fig_dist = create_keyword_distribution(results)
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # Top Opportunities Chart
    st.subheader("🏆 Top 20 Opportunities by Volume")
    fig_top = create_opportunity_chart(results.head(20))
    st.plotly_chart(fig_top, use_container_width=True)
    
    # Keyword difficulty analysis (if API data available)
    if 'Avg Difficulty' in results.columns:
        st.subheader("📈 Difficulty vs Opportunity Analysis")
        # Scatter plot implementation would go here

def show_help():
    st.header("📚 How to Use This Tool")
    
    with st.expander("Getting Started", expanded=True):
        st.markdown("""
        ### Step 1: Prepare Your Data
        
        **Keyword Export Requirements:**
        - CSV format from Ahrefs, SEMrush, or similar
        - Must contain: URL, Keyword, Search Volume, Position
        - Optional: Keyword Difficulty, CPC, etc.
        
        **Crawl Export Requirements:**
        - CSV format from Screaming Frog or similar
        - Must contain: URL/Address, Title, H1, Page Content
        - Enable custom extraction for page copy
        """)
    
    with st.expander("Understanding the Results"):
        st.markdown("""
        ### What is "Striking Distance"?
        
        Keywords in striking distance are those ranking in positions 4-20 that could 
        potentially move to the first page with minimal optimization effort.
        
        ### Key Metrics:
        - **Striking Dist. Vol**: Combined search volume of all keywords in range
        - **KWs in Striking Dist.**: Count of keywords within the position range
        - **Difficulty**: Average keyword difficulty (when API is enabled)
        
        ### Optimization Flags:
        - ✅ **True**: Keyword appears in the element
        - ❌ **False**: Keyword missing from the element (optimization opportunity)
        """)
    
    with st.expander("API Integration"):
        st.markdown("""
        ### Why Use API Integration?
        
        API integration provides real-time data for:
        - Accurate search volumes
        - Keyword difficulty scores
        - Competition metrics
        - SERP features
        
        ### Supported APIs:
        1. **DataForSEO**: Best for bulk keyword data
        2. **SEMrush**: Comprehensive competitive data
        3. **Ahrefs**: Detailed backlink and keyword metrics
        """)

if __name__ == "__main__":
    main()
