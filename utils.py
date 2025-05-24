"""
Utility classes for SEO Striking Distance Analyzer
Includes data processing, keyword analysis, and API integration
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import requests
import json
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from functools import lru_cache
import streamlit as st

class DataProcessor:
    """Handles data loading and preprocessing with improved efficiency"""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.column_mappings = {
            'ahrefs': {
                'Current position': 'Position',
                'Current URL': 'URL',
                'Search Volume': 'Volume'
            },
            'semrush': {
                'Position': 'Position',
                'URL': 'URL',
                'Search Volume': 'Volume',
                'Keyword': 'Keyword'
            }
        }
    
    @st.cache_data
    def load_keyword_data(_self, file) -> pd.DataFrame:
        """Load and standardize keyword data with caching"""
        # Read CSV with optimized dtypes
        df = pd.read_csv(
            file,
            dtype={
                'URL': 'str',
                'Keyword': 'str',
                'Volume': 'object',  # Handle mixed types
                'Position': 'float32'
            },
            low_memory=False
        )
        
        # Detect and apply column mappings
        df = _self._standardize_columns(df)
        
        # Clean and optimize data
        df = _self._clean_keyword_data(df)
        
        return df
    
    @st.cache_data
    def load_crawl_data(_self, file) -> pd.DataFrame:
        """Load and standardize crawl data with caching"""
        df = pd.read_csv(file, dtype='str', low_memory=False)
        
        # Standardize column names
        column_map = {
            'Address': 'URL',
            'Title 1': 'Title',
            'H1-1': 'H1',
            'Copy 1': 'Copy'
        }
        df.rename(columns=column_map, inplace=True)
        
        # Keep only necessary columns
        cols = ['URL', 'Title', 'H1', 'Copy', 'Indexability']
        available_cols = [col for col in cols if col in df.columns]
        df = df[available_cols]
        
        # Filter indexable pages only
        if 'Indexability' in df.columns:
            df = df[df['Indexability'] != 'Non-Indexable']
        
        # Clean text data
        text_cols = ['Title', 'H1', 'Copy']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna('').str.lower().str.strip()
        
        return df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Auto-detect and standardize column names"""
        # Try each mapping set
        for tool, mapping in self.column_mappings.items():
            if all(col in df.columns for col in mapping.keys()):
                df.rename(columns=mapping, inplace=True)
                break
        
        return df
    
    def _clean_keyword_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and filter keyword data efficiently"""
        # Handle mixed volume data (e.g., "0-10" from Ahrefs)
        if df['Volume'].dtype == 'object':
            df['Volume'] = df['Volume'].astype(str).str.replace('0-10', '0')
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        
        # Remove invalid rows
        df = df.dropna(subset=['URL', 'Keyword', 'Volume', 'Position'])
        
        # Apply filters using vectorized operations
        mask = (
            (df['Volume'] >= self.settings['min_volume']) &
            (df['Position'] >= self.settings['min_position']) &
            (df['Position'] <= self.settings['max_position'])
        )
        
        # Filter pagination URLs if specified
        if self.settings['pagination_filters']:
            filters = self.settings['pagination_filters'].split('|')
            pagination_mask = ~df['URL'].str.contains('|'.join(filters), na=False)
            mask = mask & pagination_mask
        
        return df[mask].copy()

class KeywordAnalyzer:
    """Analyzes keywords with improved efficiency and API integration"""
    
    def __init__(self, df_keywords: pd.DataFrame, df_crawl: pd.DataFrame, 
                 settings: Dict, api_client: Optional['APIClient'] = None):
        self.df_keywords = df_keywords
        self.df_crawl = df_crawl
        self.settings = settings
        self.api_client = api_client
    
    def analyze(self) -> pd.DataFrame:
        """Main analysis with optimized processing"""
        # Group keywords efficiently
        grouped = self._group_keywords()
        
        # Get top keywords per URL
        top_keywords = self._get_top_keywords()
        
        # Merge with crawl data
        results = self._merge_with_crawl(grouped, top_keywords)
        
        # Check keyword presence (vectorized)
        results = self._check_keyword_presence(results)
        
        # Apply final filters
        if self.settings['drop_all_true']:
            results = self._drop_fully_optimized(results)
        
        return results
    
    def _group_keywords(self) -> pd.DataFrame:
        """Group keywords by URL with aggregations"""
        agg_funcs = {
            'Volume': 'sum',
            'Keyword': 'count'
        }
        
        grouped = self.df_keywords.groupby('URL').agg(agg_funcs).reset_index()
        grouped.rename(columns={
            'Volume': 'Striking Dist. Vol',
            'Keyword': 'KWs in Striking Dist.'
        }, inplace=True)
        
        return grouped
    
    def _get_top_keywords(self) -> pd.DataFrame:
        """Get top 5 keywords per URL efficiently"""
        # Sort by URL and Volume descending
        sorted_df = self.df_keywords.sort_values(['URL', 'Volume'], ascending=[True, False])
        
        # Get top 5 per URL using groupby
        top_kws = sorted_df.groupby('URL').head(5)
        
        # Create pivot table for keyword columns
        top_kws['rank'] = top_kws.groupby('URL').cumcount() + 1
        
        # Pivot for keywords
        kw_pivot = top_kws.pivot(index='URL', columns='rank', values='Keyword')
        kw_pivot.columns = [f'KW{i}' for i in range(1, 6)]
        
        # Pivot for volumes
        vol_pivot = top_kws.pivot(index='URL', columns='rank', values='Volume')
        vol_pivot.columns = [f'KW{i} Vol' for i in range(1, 6)]
        
        # Combine
        result = pd.concat([kw_pivot, vol_pivot], axis=1)
        result = result.reset_index()
        
        return result
    
    def _merge_with_crawl(self, grouped: pd.DataFrame, top_keywords: pd.DataFrame) -> pd.DataFrame:
        """Merge all data together"""
        # First merge grouped with top keywords
        results = pd.merge(grouped, top_keywords, on='URL', how='left')
        
        # Then merge with crawl data
        results = pd.merge(results, self.df_crawl, on='URL', how='inner')
        
        # Reorder columns
        base_cols = ['URL', 'Title', 'H1', 'Copy', 'Striking Dist. Vol', 'KWs in Striking Dist.']
        kw_cols = []
        
        for i in range(1, 6):
            kw_cols.extend([f'KW{i}', f'KW{i} Vol'])
        
        all_cols = base_cols + kw_cols
        available_cols = [col for col in all_cols if col in results.columns]
        
        return results[available_cols]
    
    def _check_keyword_presence(self, df: pd.DataFrame) -> pd.DataFrame:
        """Check if keywords appear in title/H1/copy using vectorized operations"""
        # Create check columns
        for i in range(1, 6):
            kw_col = f'KW{i}'
            if kw_col in df.columns:
                # Handle NaN values
                df[kw_col] = df[kw_col].fillna('')
                
                # Vectorized string matching
                for element in ['Title', 'H1', 'Copy']:
                    check_col = f'{kw_col} in {element}'
                    
                    # Use vectorized string contains
                    df[check_col] = df.apply(
                        lambda row: row[kw_col].lower() in row[element] if row[kw_col] else '',
                        axis=1
                    )
        
        return df
    
    def _drop_fully_optimized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop rows where keyword appears in all elements"""
        for i in range(1, 6):
            kw_col = f'KW{i}'
            if kw_col in df.columns:
                check_cols = [f'{kw_col} in Title', f'{kw_col} in H1', f'{kw_col} in Copy']
                
                # Create mask for rows to drop
                drop_mask = (
                    (df[check_cols[0]] == True) & 
                    (df[check_cols[1]] == True) & 
                    (df[check_cols[2]] == True)
                )
                
                # Keep rows that don't match the drop condition
                df = df[~drop_mask]
        
        return df
    
    def enrich_with_api_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich results with API data for keyword difficulty and updated volumes"""
        if not self.api_client:
            return df
        
        # Collect all unique keywords
        all_keywords = []
        for i in range(1, 6):
            kw_col = f'KW{i}'
            if kw_col in df.columns:
                keywords = df[kw_col].dropna().unique().tolist()
                all_keywords.extend(keywords)
        
        # Remove duplicates and empty strings
        all_keywords = [kw for kw in set(all_keywords) if kw]
        
        if not all_keywords:
            return df
        
        # Fetch data in batches (API returns lowercase keys)
        with st.spinner(f"Fetching metrics for {len(all_keywords)} keywords..."):
            keyword_data = self.api_client.get_keyword_data_batch(all_keywords)
        
        # Update dataframe with API data
        for i in range(1, 6):
            kw_col = f'KW{i}'
            if kw_col in df.columns:
                # Add difficulty column
                df[f'{kw_col} Difficulty'] = df[kw_col].apply(
                    lambda kw: keyword_data.get(kw.lower() if pd.notna(kw) else '', {}).get('difficulty', '') if kw else ''
                )
                
                # Add CPC column
                df[f'{kw_col} CPC'] = df[kw_col].apply(
                    lambda kw: keyword_data.get(kw.lower() if pd.notna(kw) else '', {}).get('cpc', '') if kw else ''
                )
                
                # Update volume if available from API
                api_volumes = df[kw_col].apply(
                    lambda kw: keyword_data.get(kw.lower() if pd.notna(kw) else '', {}).get('volume', None) if kw else None
                )
                
                # Only update non-null API volumes
                mask = api_volumes.notna()
                if mask.any():
                    df.loc[mask, f'{kw_col} Vol'] = api_volumes[mask]
        
        # Calculate average difficulty
        difficulty_cols = [f'KW{i} Difficulty' for i in range(1, 6) if f'KW{i} Difficulty' in df.columns]
        if difficulty_cols:
            df['Avg Difficulty'] = df[difficulty_cols].replace('', np.nan).mean(axis=1)
        
        # Recalculate total volume after API updates
        vol_cols = [f'KW{i} Vol' for i in range(1, 6) if f'KW{i} Vol' in df.columns]
        if vol_cols:
            df['Striking Dist. Vol'] = df[vol_cols].fillna(0).sum(axis=1)
        
        return df

class APIClient:
    """Client for fetching keyword data from various SEO APIs"""
    
    def __init__(self, email: str, password: str, provider: str = 'dataforseo'):
        self.email = email
        self.password = password
        self.provider = provider.lower()
        self.base_url = 'https://api.dataforseo.com/v3'
        self.session = requests.Session()
        self._setup_auth()
    
    def _setup_auth(self):
        """Setup authentication for API requests"""
        # DataForSEO uses basic auth with email:password
        credentials = f"{self.email}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.session.headers['Authorization'] = f'Basic {encoded}'
        self.session.headers['Content-Type'] = 'application/json'
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self.session.get(f"{self.base_url}/appendix/user_data")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_keyword_data_batch(self, keywords: List[str], location_code: int = 2840) -> Dict:
        """
        Get data for multiple keywords efficiently.
        Batches up to 1,000 keywords per request to minimize costs.
        
        Args:
            keywords: List of keywords to fetch data for
            location_code: Location code (default 2840 for USA)
            
        Returns:
            Dict mapping keywords to their metrics
        """
        results = {}
        
        # Process in batches of up to 1,000 keywords (DataForSEO limit)
        batch_size = 1000
        
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            batch_results = self._get_dataforseo_batch(batch, location_code)
            results.update(batch_results)
        
        return results
    
    def _get_dataforseo_batch(self, keywords: List[str], location_code: int) -> Dict:
        """Get batch keyword data from DataForSEO"""
        try:
            endpoint = f"{self.base_url}/keywords_data/google_ads/search_volume/live"
            
            # Prepare request data
            data = [{
                "keywords": keywords,
                "location_code": location_code,
                "language_code": "en",
                "search_partners": False  # Don't include search partners
            }]
            
            response = self.session.post(endpoint, json=data)
            
            if response.status_code == 200:
                result = response.json()
                keyword_data = {}
                
                # Check if we have valid results
                if (result.get('tasks') and 
                    result['tasks'][0].get('result') and 
                    result['tasks'][0]['result']):
                    
                    # Process each keyword result
                    for item in result['tasks'][0]['result']:
                        keyword = item.get('keyword', '')
                        
                        # Get the most recent search volume
                        search_volume = item.get('search_volume', 0)
                        
                        # Convert competition to difficulty score (0-100)
                        competition_index = item.get('competition_index', 0)
                        
                        # Extract CPC
                        cpc = item.get('cpc', 0)
                        
                        keyword_data[keyword.lower()] = {
                            'volume': search_volume,
                            'difficulty': competition_index,
                            'cpc': cpc,
                            'competition': item.get('competition', 'UNKNOWN')
                        }
                
                return keyword_data
                
        except Exception as e:
            st.error(f"API Error: {str(e)}")
        
        return {}
