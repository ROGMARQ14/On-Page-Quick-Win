"""
Visualization functions for SEO Striking Distance Analyzer
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict

def create_opportunity_chart(df: pd.DataFrame) -> go.Figure:
    """Create horizontal bar chart of top opportunities"""
    
    # Sort by striking distance volume
    df_sorted = df.sort_values('Striking Dist. Vol', ascending=True)
    
    # Create figure
    fig = go.Figure()
    
    # Add trace
    fig.add_trace(go.Bar(
        x=df_sorted['Striking Dist. Vol'],
        y=df_sorted['URL'].apply(lambda x: x[:50] + '...' if len(x) > 50 else x),
        orientation='h',
        text=df_sorted['Striking Dist. Vol'].apply(lambda x: f'{x:,}'),
        textposition='outside',
        marker_color='#1f77b4',
        hovertemplate='<b>%{y}</b><br>' +
                      'Search Volume: %{x:,}<br>' +
                      '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title='Top Keyword Opportunities by Search Volume',
        xaxis_title='Total Search Volume',
        yaxis_title='Page URL',
        height=600,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
        ),
        yaxis=dict(
            showgrid=False,
        )
    )
    
    return fig

def create_keyword_distribution(df: pd.DataFrame) -> go.Figure:
    """Create distribution chart of keywords per page"""
    
    # Create bins for keyword counts
    bins = [1, 5, 10, 20, 50, 100, df['KWs in Striking Dist.'].max() + 1]
    labels = ['1-4', '5-9', '10-19', '20-49', '50-99', '100+']
    
    df['KW Range'] = pd.cut(df['KWs in Striking Dist.'], bins=bins, labels=labels, include_lowest=True)
    
    # Group by range
    distribution = df.groupby('KW Range').agg({
        'URL': 'count',
        'Striking Dist. Vol': 'sum'
    }).reset_index()
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add bar trace for page count
    fig.add_trace(go.Bar(
        x=distribution['KW Range'],
        y=distribution['URL'],
        name='Page Count',
        marker_color='#2ca02c',
        yaxis='y',
        text=distribution['URL'],
        textposition='outside',
    ))
    
    # Add line trace for total volume
    fig.add_trace(go.Scatter(
        x=distribution['KW Range'],
        y=distribution['Striking Dist. Vol'],
        name='Total Volume',
        mode='lines+markers',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=10),
        yaxis='y2'
    ))
    
    # Update layout
    fig.update_layout(
        title='Keyword Distribution Analysis',
        xaxis_title='Keywords per Page',
        yaxis_title='Number of Pages',
        yaxis2=dict(
            title='Total Search Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        height=500,
        legend=dict(
            x=0.7,
            y=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
        )
    )
    
    return fig

def create_difficulty_scatter(df: pd.DataFrame) -> go.Figure:
    """Create scatter plot of difficulty vs opportunity"""
    
    if 'Avg Difficulty' not in df.columns:
        return go.Figure()
    
    # Create figure
    fig = go.Figure()
    
    # Add scatter trace
    fig.add_trace(go.Scatter(
        x=df['Avg Difficulty'],
        y=df['Striking Dist. Vol'],
        mode='markers',
        marker=dict(
            size=df['KWs in Striking Dist.'] * 2,
            color=df['Striking Dist. Vol'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title="Search Volume"
            ),
            line=dict(width=1, color='white')
        ),
        text=df['URL'].apply(lambda x: x[:30] + '...' if len(x) > 30 else x),
        hovertemplate='<b>%{text}</b><br>' +
                      'Difficulty: %{x:.1f}<br>' +
                      'Volume: %{y:,}<br>' +
                      '<extra></extra>'
    ))
    
    # Add quadrant lines
    avg_diff = df['Avg Difficulty'].mean()
    avg_vol = df['Striking Dist. Vol'].mean()
    
    fig.add_hline(y=avg_vol, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=avg_diff, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Add quadrant labels
    fig.add_annotation(
        x=avg_diff * 0.5, y=avg_vol * 1.5,
        text="Easy Wins", showarrow=False,
        font=dict(size=14, color="green")
    )
    fig.add_annotation(
        x=avg_diff * 1.5, y=avg_vol * 1.5,
        text="High Competition", showarrow=False,
        font=dict(size=14, color="orange")
    )
    
    # Update layout
    fig.update_layout(
        title='Opportunity vs Difficulty Analysis',
        xaxis_title='Average Keyword Difficulty',
        yaxis_title='Total Search Volume',
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            range=[0, 100]
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            type='log'
        )
    )
    
    return fig

def create_optimization_matrix(df: pd.DataFrame) -> go.Figure:
    """Create heatmap showing optimization status"""
    
    # Prepare data for heatmap
    optimization_data = []
    
    for idx, row in df.head(20).iterrows():
        page_data = []
        for i in range(1, 6):
            kw_col = f'KW{i}'
            if kw_col in df.columns and row[kw_col]:
                title_check = 1 if row.get(f'{kw_col} in Title', False) == True else 0
                h1_check = 1 if row.get(f'{kw_col} in H1', False) == True else 0
                copy_check = 1 if row.get(f'{kw_col} in Copy', False) == True else 0
                
                # Calculate optimization score (0-3)
                score = title_check + h1_check + copy_check
                page_data.append(score)
            else:
                page_data.append(-1)  # No keyword
        
        optimization_data.append(page_data)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=optimization_data,
        x=['KW1', 'KW2', 'KW3', 'KW4', 'KW5'],
        y=df.head(20)['URL'].apply(lambda x: x[:30] + '...' if len(x) > 30 else x),
        colorscale=[
            [0, 'lightgray'],      # No keyword
            [0.25, 'red'],         # Not optimized
            [0.5, 'orange'],       # Partially optimized
            [0.75, 'yellow'],      # Mostly optimized
            [1, 'green']           # Fully optimized
        ],
        text=[[f'{val if val >= 0 else "N/A"}' for val in row] for row in optimization_data],
        texttemplate='%{text}',
        textfont=dict(size=12),
        colorbar=dict(
            title="Optimization<br>Score",
            tickmode='array',
            tickvals=[0, 1, 2, 3],
            ticktext=['None', 'Low', 'Medium', 'High']
        )
    ))
    
    # Update layout
    fig.update_layout(
        title='Keyword Optimization Status Matrix',
        xaxis_title='Keywords',
        yaxis_title='Pages',
        height=600,
        xaxis=dict(side='top')
    )
    
    return fig
