# SEO Striking Distance Keyword Finder

A Streamlit application that helps SEO professionals identify "striking distance" keyword opportunities - keywords that are ranking in positions 4-20 and could be improved with targeted optimization.

## Overview

This tool helps you:

1. Identify which pages on your site have keywords ranking in positions 4-20 (configurable)
2. Find opportunities where keywords aren't properly utilized in titles, H1s, or content
3. Prioritize by search volume and opportunity size

## Features

- User-friendly Streamlit interface with configuration options
- Support for keyword exports from Ahrefs, Semrush, and other SEO tools
- Compatible with Screaming Frog crawl exports
- Customizable position range and minimum search volume
- Option to filter out keywords already used in title, H1, and content
- CSV export of results for further analysis

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:

```bash
streamlit run app.py
```

2. Upload your keyword export CSV file (from Ahrefs, Semrush, etc.)
3. Upload your site crawl export CSV file (from Screaming Frog or similar)
4. Configure the settings in the sidebar as needed
5. Review the results and download the CSV file for your optimization plan

## Required Data Formats

### Keyword Export
The keyword export should contain at least these columns:
- URL or Current URL: The URL of the page
- Keyword: The target keyword
- Volume or Search Volume: Monthly search volume
- Position or Current position: Current ranking position

### Crawl Export
The crawl export should contain at least these columns:
- Address: The URL of the page
- Indexability: Whether the page is indexable
- Title 1: The page title
- H1-1: The primary H1 heading
- Copy 1: The page content (requires custom extraction in Screaming Frog)

## Credits

This tool is based on the Python + Streamlit SEO striking distance concept from Search Engine Journal.

## License

MIT
