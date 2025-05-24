import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from typing import Union
from pandas import DataFrame, Series

# Set page configuration
st.set_page_config(
    page_title="SEO Striking Distance Tool",
    page_icon="📈",
    layout="wide"
)

# App title and description
st.title("SEO Striking Distance Keyword Finder")
st.markdown("""
This app helps you identify SEO striking distance keyword opportunities.
Upload your keyword export and site crawl data to find optimization opportunities.
""")

# Sidebar for configuration options
st.sidebar.header("Configuration")

# Set the variables in the sidebar
min_volume = st.sidebar.number_input("Minimum Search Volume", min_value=0, value=10)
min_position = st.sidebar.number_input("Minimum Position", min_value=1, value=4)
max_position = st.sidebar.number_input("Maximum Position", min_value=1, value=20)
drop_all_true = st.sidebar.checkbox("Remove if keyword already in Title, H1 & Copy", value=True)
pagination_filters = st.sidebar.text_input("Pagination Filter Patterns", value="filterby|page|p=")

# Advanced settings expander
with st.sidebar.expander("Advanced Settings"):
    max_keywords = st.number_input("Max Keywords per URL", min_value=1, value=5)

# Function to download dataframe as CSV
def get_csv_download_link(df, filename="data.csv", link_text="Download CSV file"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

# Upload keyword export file
st.header("Step 1: Upload Keyword Export")
st.markdown("Upload your keyword export from Ahrefs, Semrush, or other SEO tools.")
keyword_file = st.file_uploader("Choose a CSV file with keyword data", type=["csv"], key="keywords")

# Upload crawl export file
st.header("Step 2: Upload Site Crawl Data")
st.markdown("Upload your website crawl export from Screaming Frog or similar tools.")
crawl_file = st.file_uploader("Choose a CSV file with crawl data", type=["csv"], key="crawl")

# Process data when both files are uploaded
if keyword_file is not None and crawl_file is not None:
    st.header("Processing Data")
    
    # Progress bar for data processing
    progress_bar = st.progress(0)
    
    try:
        # Load keyword data
        df_keywords = pd.read_csv(
            keyword_file,
            on_bad_lines='skip',  # Updated parameter name from error_bad_lines
            low_memory=False,
            encoding="utf8",
            dtype={
                "URL": "str",
                "Keyword": "str",
                "Volume": "str",
                "Position": int,
                "Current URL": "str",
                "Search Volume": int,
            },
        )
        
        progress_bar.progress(20)
        st.write("Keyword data loaded successfully!")
        
        # Standardize keyword data columns
        df_keywords.rename(
            columns={
                "Current position": "Position",
                "Current URL": "URL",
                "Search Volume": "Volume",
            },
            inplace=True,
        )

        # Keep only necessary columns
        cols = ["URL", "Keyword", "Volume", "Position"]
        df_keywords = df_keywords.reindex(columns=cols)

        # Clean volume data (handles Ahrefs format)
        try:
            df_keywords["Volume"] = df_keywords["Volume"].str.replace("0-10", "0", regex=False)
        except AttributeError:
            pass
        
        progress_bar.progress(40)
        
        # Clean the keyword data
        df_keywords = df_keywords[df_keywords["URL"].notna()]  # remove any missing values
        df_keywords = df_keywords[df_keywords["Volume"].notna()]  # remove any missing values
        df_keywords = df_keywords.astype({"Volume": int})  # change data type to int
        df_keywords = df_keywords.sort_values(by="Volume", ascending=False)  # sort by highest vol
        
        # Create dataframe to merge search volume back in later
        df_keyword_vol = df_keywords[["Keyword", "Volume"]]
        
        # Filter by minimum search volume
        df_keywords.loc[df_keywords["Volume"] < min_volume, "Volume_Too_Low"] = "drop"
        df_keywords = df_keywords[~df_keywords["Volume_Too_Low"].isin(["drop"])]
        
        # Filter by position range
        df_keywords.loc[df_keywords["Position"] < min_position, "Position_Too_High"] = "drop"
        df_keywords = df_keywords[~df_keywords["Position_Too_High"].isin(["drop"])]
        df_keywords.loc[df_keywords["Position"] > max_position, "Position_Too_Low"] = "drop"
        df_keywords = df_keywords[~df_keywords["Position_Too_Low"].isin(["drop"])]
        
        progress_bar.progress(60)
        
        # Load crawl data
        df_crawl = pd.read_csv(
            crawl_file,
            on_bad_lines='skip',  # Updated parameter name from error_bad_lines
            low_memory=False,
            encoding="utf8",
            dtype="str",
        )
        
        st.write("Crawl data loaded successfully!")
        
        # Keep only necessary columns from crawl data
        try:
            cols = ["Address", "Indexability", "Title 1", "H1-1", "Copy 1"]
            df_crawl = df_crawl.reindex(columns=cols)
            # Drop non-indexable rows
            df_crawl = df_crawl[~df_crawl["Indexability"].isin(["Non-Indexable"])]
            # Standardize column names
            df_crawl.rename(columns={"Address": "URL", "Title 1": "Title", "H1-1": "H1", "Copy 1": "Copy"}, inplace=True)
        except KeyError:
            st.error("Crawl file doesn't have the expected columns. Please ensure it contains: Address, Indexability, Title 1, H1-1, Copy 1")
            st.stop()
        
        progress_bar.progress(80)
        
        # Group keywords
        df_keywords_group = df_keywords.copy()
        df_keywords_group["KWs in Striking Dist."] = 1  # Count keywords in striking distance
        df_keywords_group = (
            df_keywords_group.groupby("URL")
            .agg({"Volume": "sum", "KWs in Striking Dist.": "count"})
            .reset_index()
        )
        
        # Create a dataframe with keywords in adjacent rows
        df_merged_all_kws = df_keywords_group.merge(
            df_keywords.groupby("URL")["Keyword"]
            .apply(lambda x: x.reset_index(drop=True))
            .unstack()
            .reset_index()
        )
        
        # Sort by biggest opportunity
        df_merged_all_kws = df_merged_all_kws.sort_values(
            by="KWs in Striking Dist.", ascending=False
        )
        
        # Reindex columns to keep just the top N keywords
        cols = ["URL", "Volume", "KWs in Striking Dist."] + list(range(max_keywords))
        df_merged_all_kws = df_merged_all_kws.reindex(columns=cols)
        
        # Create column rename dictionary for keywords
        rename_dict = {
            "Volume": "Striking Dist. Vol",
        }
        for i in range(max_keywords):
            rename_dict[i] = f"KW{i+1}"
        
        # Rename columns
        df_striking: Union[Series, DataFrame, None] = df_merged_all_kws.rename(
            columns=rename_dict
        )
        
        # Merge with crawl data
        df_striking = pd.merge(df_striking, df_crawl, on="URL", how="inner")
        
        # Set up final column order
        cols = ["URL", "Title", "H1", "Copy", "Striking Dist. Vol", "KWs in Striking Dist."]
        
        # Add keyword columns and their associated columns
        for i in range(1, max_keywords + 1):
            cols.extend([
                f"KW{i}", 
                f"KW{i} Vol", 
                f"KW{i} in Title", 
                f"KW{i} in H1", 
                f"KW{i} in Copy"
            ])
        
        # Reindex columns
        df_striking = df_striking.reindex(columns=cols)
        
        # Merge in keyword volume data for each keyword column
        for i in range(1, max_keywords + 1):
            kw_col = f"KW{i}"
            vol_col = f"KW{i} Vol"
            
            df_striking = pd.merge(df_striking, df_keyword_vol, left_on=kw_col, right_on="Keyword", how="left")
            df_striking[vol_col] = df_striking['Volume']
            df_striking.drop(['Keyword', 'Volume'], axis=1, inplace=True)
        
        # Fill NaN values with empty strings
        df_striking = df_striking.fillna("")
        
        # Convert Title, H1, and Copy to lowercase for keyword matching
        df_striking["Title"] = df_striking["Title"].str.lower()
        df_striking["H1"] = df_striking["H1"].str.lower()
        df_striking["Copy"] = df_striking["Copy"].str.lower()
        
        # Check if keywords appear in Title, H1, and Copy
        for i in range(1, max_keywords + 1):
            kw_col = f"KW{i}"
            title_col = f"KW{i} in Title"
            h1_col = f"KW{i} in H1"
            copy_col = f"KW{i} in Copy"
            
            df_striking[title_col] = df_striking.apply(lambda row: row[kw_col] in row["Title"] if row[kw_col] else "", axis=1)
            df_striking[h1_col] = df_striking.apply(lambda row: row[kw_col] in row["H1"] if row[kw_col] else "", axis=1)
            df_striking[copy_col] = df_striking.apply(lambda row: row[kw_col] in row["Copy"] if row[kw_col] else "", axis=1)
            
            # Delete true/false values if there is no keyword
            df_striking.loc[df_striking[kw_col] == "", [title_col, h1_col, copy_col]] = ""
        
        # Define function to drop rows if all values are True
        def true_dropper(col1, col2, col3):
            drop = df_striking.drop(
                df_striking[
                    (df_striking[col1] == True)
                    & (df_striking[col2] == True)
                    & (df_striking[col3] == True)
                ].index
            )
            return drop
        
        # Drop rows if all values are True (if enabled)
        if drop_all_true:
            for i in range(1, max_keywords + 1):
                title_col = f"KW{i} in Title"
                h1_col = f"KW{i} in H1"
                copy_col = f"KW{i} in Copy"
                df_striking = true_dropper(title_col, h1_col, copy_col)
        
        progress_bar.progress(100)
        
        # Display results
        st.header("Results")
        st.write(f"Found {len(df_striking)} pages with striking distance keywords.")
        
        # Display the dataframe
        st.dataframe(df_striking)
        
        # Provide download link
        st.markdown(get_csv_download_link(df_striking, "Keywords_in_Striking_Distance.csv", "Download CSV file"), unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"An error occurred during processing: {e}")
else:
    st.info("Please upload both keyword export and crawl data files to continue.")

# Footer
st.markdown("---")
st.markdown("SEO Striking Distance Tool - Based on the article from Search Engine Journal")
