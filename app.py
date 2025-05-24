"""
SEO Striking Distance Analyzer - Enhanced Version
An improved tool for finding keyword optimization opportunities
"""

import streamlit as st

# Set page config first - this loads quickly
st.set_page_config(
    page_title="SEO Striking Distance Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize basic session state variables - lightweight operations
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
    
if 'settings' not in st.session_state:
    st.session_state.settings = {
        'min_volume': 10,
        'min_position': 4,
        'max_position': 20,
        'drop_all_true': True,
        'pagination_filters': 'filterby|page|p=',
        'api_enabled': False
    }

if 'api_client' not in st.session_state:
    st.session_state.api_client = None

# App title - loads immediately
st.title("🎯 SEO Striking Distance Analyzer")
st.markdown("Find and optimize your best keyword opportunities")

# Import required modules only when needed, not at the top of the file
def main():
    # Create sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Position range settings
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
                    # Import APIClient only when needed
                    from utils import APIClient
                    
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
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["📊 Analysis", "📈 Visualizations", "📚 Help"])
    
    with tab1:
        run_analysis()
    
    with tab2:
        show_visualizations()
    
    with tab3:
        show_help()

def run_analysis():
    # Upload files
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ Upload Keyword Export")
        keyword_file = st.file_uploader(
            "Upload CSV from Ahrefs/SEMrush",
            type=['csv'],
            help="Export all organic keywords from Ahrefs/SEMrush"
        )
    
    with col2:
        st.subheader("2️⃣ Upload Website Crawl")
        crawl_file = st.file_uploader(
            "Upload CSV from Screaming Frog",
            type=['csv'],
            help="Export from Screaming Frog with URL, Title, H1, and Body"
        )
    
    # Process data when files are uploaded
    if keyword_file and crawl_file:
        if st.button("🚀 Run Analysis", type="primary"):
            # Import heavy modules only when actually processing data
            import pandas as pd
            import numpy as np
            from datetime import datetime
            from utils import DataProcessor, KeywordAnalyzer
            
            with st.spinner("Processing data..."):
                try:
                    # Setup progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Step 1: Process keyword data
                    status_text.text("Loading and processing keyword data...")
                    processor = DataProcessor()
                    df_keywords = processor.load_keyword_data(keyword_file, st.session_state.settings)
                    progress_bar.progress(0.2)
                    
                    # Step 2: Process crawl data
                    status_text.text("Loading and processing crawl data...")
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

def display_results(results):
    import pandas as pd
    from datetime import datetime
    import io
    
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
        min_vol = st.number_input(
            "Min Volume", 
            min_value=0, 
            value=int(results['Striking Dist. Vol'].min())
        )
    
    with col2:
        max_vol = st.number_input(
            "Max Volume",
            min_value=int(min_vol),
            value=int(results['Striking Dist. Vol'].max())
        )
    
    with col3:
        kw_filter = st.selectbox(
            "Filter Keywords",
            options=["All", "With Opportunities Only", "Without Any Optimization"]
        )
    
    # Apply filters
    filtered_df = results.copy()
    
    # Volume filter
    filtered_df = filtered_df[
        (filtered_df['Striking Dist. Vol'] >= min_vol) & 
        (filtered_df['Striking Dist. Vol'] <= max_vol)
    ]
    
    # Keyword opportunity filter
    if kw_filter == "With Opportunities Only":
        # Find rows with at least one 'False' in keyword checks
        mask = pd.Series(False, index=filtered_df.index)
        for i in range(1, 6):
            for element in ['Title', 'H1', 'Copy']:
                col = f'KW{i} in {element}'
                if col in filtered_df.columns:
                    mask = mask | (filtered_df[col] == False)
        
        filtered_df = filtered_df[mask]
        
    elif kw_filter == "Without Any Optimization":
        # Find rows with no 'True' in keyword checks
        mask = pd.Series(True, index=filtered_df.index)
        for i in range(1, 6):
            for element in ['Title', 'H1', 'Copy']:
                col = f'KW{i} in {element}'
                if col in filtered_df.columns:
                    mask = mask & (filtered_df[col] != True)
        
        filtered_df = filtered_df[mask]
    
    # Show visualization if we have data
    if not filtered_df.empty and len(filtered_df) > 0:
        with st.expander("📊 Opportunity Visualization", expanded=True):
            st.subheader("Top Striking Distance Opportunities")
            
            # Import visualization only when needed
            from visualizations import create_opportunity_chart
            
            fig = create_opportunity_chart(filtered_df)
            st.plotly_chart(fig, use_container_width=True)
    
    # Show result table
    st.subheader("📋 Detailed Results")
    if not filtered_df.empty:
        # Prepare display columns
        base_cols = ['URL', 'Title', 'Striking Dist. Vol', 'KWs in Striking Dist.']
        kw_cols = []
        
        for i in range(1, 6):
            kw_base = f'KW{i}'
            vol_col = f'{kw_base} Vol'
            diff_col = f'{kw_base} Difficulty'
            cpc_col = f'{kw_base} CPC'
            
            if kw_base in filtered_df.columns:
                kw_cols.extend([kw_base, vol_col])
                
                if diff_col in filtered_df.columns:
                    kw_cols.append(diff_col)
                    
                if cpc_col in filtered_df.columns:
                    kw_cols.append(cpc_col)
                
                for element in ['Title', 'H1', 'Copy']:
                    check_col = f'{kw_base} in {element}'
                    if check_col in filtered_df.columns:
                        kw_cols.append(check_col)
        
        display_cols = base_cols + [col for col in kw_cols if col in filtered_df.columns]
        
        # Show dataframe
        st.dataframe(filtered_df[display_cols], use_container_width=True)
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "📥 Download Results (CSV)",
                data=csv,
                file_name=f"striking_distance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Excel export using minimal dependencies
            try:
                # Import Excel libraries only when needed
                from io import BytesIO
                
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    filtered_df.to_excel(writer, index=False, sheet_name='Striking Distance')
                
                buffer.seek(0)
                st.download_button(
                    "📥 Download Results (Excel)",
                    data=buffer,
                    file_name=f"striking_distance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
            except Exception as e:
                st.error(f"Excel export error: {str(e)}")
    else:
        st.info("No results match your filters. Try adjusting your criteria.")

def show_visualizations():
    if st.session_state.processed_data is not None:
        # Import visualization functions only when needed
        from visualizations import create_opportunity_chart, create_keyword_distribution
        
        results = st.session_state.processed_data
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top URL Opportunities")
            fig1 = create_opportunity_chart(results)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("Keyword Distribution")
            fig2 = create_keyword_distribution(results)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Run the analysis first to view visualizations")

def show_help():
    st.subheader("📚 How to Use This Tool")
    
    with st.expander("Step 1: Export Your Data", expanded=True):
        st.markdown("""
        ### Keyword Export
        1. **Ahrefs**: Go to Organic Keywords report > Export all rows as CSV
        2. **SEMrush**: Go to Organic Research > Positions > Export to CSV
        
        Ensure your export has these columns:
        - URL/Current URL
        - Keyword
        - Position/Current Position
        - Volume/Search Volume
        """)
        
        st.markdown("""
        ### Website Crawl
        1. **Screaming Frog**: Run a crawl of your site
        2. **Configuration**:
           - Enable extraction of H1 and Title 
           - Add custom extraction for page copy (CSS: body)
        3. **Export**: Save as CSV with all columns
        """)
    
    with st.expander("Step 2: Analyze Your Data"):
        st.markdown("""
        1. **Upload Both Files**: Use the upload buttons on the Analysis tab
        2. **Configure Settings**:
           - Min/Max Position: Define your "striking distance" range
           - Min Volume: Filter out low-volume keywords
           - Advanced Settings: Additional filtering options
        3. **API Integration**: Connect to DataForSEO for real-time metrics
        4. **Run Analysis**: Click the button to generate results
        """)
    
    with st.expander("Step 3: Interpret Results"):
        st.markdown("""
        ### Key Metrics:
        - **Striking Dist. Vol**: Combined search volume of keywords in range
        - **KWs in Striking Dist**: Number of keywords within position range
        - **Avg Difficulty**: Average keyword difficulty (with API)
        
        ### Optimization Status:
        - ✅ **True**: Keyword is found in the element
        - ❌ **False**: Optimization opportunity
        - **Blank**: No keyword to check
        """)
        
        st.markdown("""
        ### Prioritize Opportunities:
        1. Focus on high-volume, low-difficulty keywords
        2. Look for pages with multiple keywords in striking distance
        3. Target keywords missing from title and H1 first
        """)
    
    with st.expander("Step 4: Download & Share"):
        st.markdown("""
        ### Export Options:
        - **CSV Export**: Basic data export
        - **Excel Export**: Formatted with conditional formatting
        
        ### Recommended Workflow:
        1. Share with content team for implementation
        2. Track changes in a project management tool
        3. Re-run analysis after 4-6 weeks to measure progress
        """)

# Run the app
if __name__ == "__main__":
    main()
