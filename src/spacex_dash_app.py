import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import os


file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw', 'spacex_launch_dash.csv')

spacex_df = pd.read_csv(file_path)

max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()


app = dash.Dash(__name__)


colors = {
    'background': '#111111',
    'text': '#FFFF99',
    'plot_background': '#222222',
    'plot_paper_bgcolor': '#111111',
    'dropdown_background': '#333333',
    'dropdown_text': '#CCFFCC',
    'grid_color': '#444444',
    'pie_colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'],
    'scatter_colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
}

# Estilos personalizados
app.layout = html.Div(style={
    'backgroundColor': colors['background'],
    'color': colors['text'],
    'margin': '0px',
    'padding': '20px',
    'fontFamily': 'Roboto, sans-serif'
}, children=[
    html.H1('SpaceX Launch Records Dashboard',
            style={'textAlign': 'center', 'color': colors['text'], 'fontSize': 40}),
    
    dcc.Dropdown(
        id='site-dropdown',
        options=[
            {'label': 'All Sites', 'value': 'All Sites'},
            {'label': 'CCAFS LC-40', 'value': 'CCAFS LC-40'},
            {'label': 'VAFB SLC-4E', 'value': 'VAFB SLC-4E'},
            {'label': 'KSC LC-39A', 'value': 'KSC LC-39A'},
            {'label': 'CCAFS SLC-40', 'value': 'CCAFS SLC-40'}
        ],
        placeholder='Select a Launch Site Here',
        value='All Sites',
        searchable=True,
        style={
            'backgroundColor': colors['dropdown_background'],
            'color': colors['dropdown_text'],
            'border': f'1px solid {colors["text"]}',
        },
        className='dropdown'
    ),
    html.Br(),

    html.Div(dcc.Graph(id='success-pie-chart')),
    html.Br(),

    html.P("Payload range (Kg):", style={'color': colors['text']}),
    dcc.RangeSlider(
        id='payload-slider',
        min=0, max=10000, step=1000,
        marks={i: {'label': str(i), 'style': {'color': colors['text']}} for i in range(0, 10001, 1000)},
        value=[min_payload, max_payload]
    ),

    html.Div(dcc.Graph(id='success-payload-scatter-chart'))
])


app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: #111111;
                font-family: 'Roboto', sans-serif;
            }
            .dropdown .Select-control {
                background-color: #333333;
            }
            .dropdown .Select-menu-outer {
                background-color: #333333;
            }
            .dropdown .Select-value-label {
                color: #CCFFCC !important;
            }
            .dropdown .Select-menu-outer .Select-option {
                background-color: #333333;
                color: #CCFFCC;
            }
            .dropdown .Select-menu-outer .Select-option:hover {
                background-color: #555555;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

@app.callback(
    Output(component_id='success-pie-chart', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value')
)
def get_pie_chart(launch_site):
    if launch_site == 'All Sites':
        data = spacex_df.groupby('Launch Site')['class'].mean().reset_index()
        fig = go.Figure(data=[go.Pie(
            labels=data['Launch Site'], 
            values=data['class'], 
            hole=.3, 
            marker_colors=colors['pie_colors']
        )])
        title = 'Total Success Launches by Site'
    else:
        data = spacex_df[spacex_df['Launch Site']==str(launch_site)]['class'].value_counts().reset_index()
        fig = go.Figure(data=[go.Pie(
            labels=data['class'], 
            values=data['count'], 
            hole=.3, 
            marker_colors=colors['pie_colors']
        )])
        title = f'Total Success Launches for Site {launch_site}'
    
    fig.update_layout(
        title=title,
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['plot_paper_bgcolor'],
        font_color=colors['text'],
        font_family='Roboto, sans-serif'
    )
    fig.update_traces(textposition='inside', textinfo='percent+label', textfont_color='black')
    return fig

@app.callback(
    Output(component_id='success-payload-scatter-chart', component_property='figure'),
    [Input(component_id='site-dropdown', component_property='value'),
     Input(component_id='payload-slider', component_property='value')]
)
def get_payload_chart(launch_site, payload_mass):
    if launch_site == 'All Sites':
        df = spacex_df[spacex_df['Payload Mass (kg)'].between(payload_mass[0], payload_mass[1])]
    else:
        df = spacex_df[(spacex_df['Launch Site']==str(launch_site)) & 
                       (spacex_df['Payload Mass (kg)'].between(payload_mass[0], payload_mass[1]))]
    
    fig = go.Figure()
    
    for i, booster in enumerate(df['Booster Version Category'].unique()):
        df_booster = df[df['Booster Version Category'] == booster]
        fig.add_trace(go.Scatter(
            x=df_booster['Payload Mass (kg)'],
            y=df_booster['class'],
            mode='markers',
            name=booster,
            text=df_booster['Launch Site'],
            marker=dict(size=10, color=colors['scatter_colors'][i % len(colors['scatter_colors'])])
        ))
    
    fig.update_layout(
        title='Correlation Between Payload and Success for ' + ('All Sites' if launch_site == 'All Sites' else launch_site),
        xaxis_title='Payload Mass (kg)',
        yaxis_title='Class',
        plot_bgcolor=colors['plot_background'],
        paper_bgcolor=colors['plot_paper_bgcolor'],
        font_color=colors['text'],
        font_family='Roboto, sans-serif',
        legend=dict(
            font=dict(color=colors['text'])
        )
    )
    
    fig.update_xaxes(
        showgrid=True,
        gridcolor=colors['grid_color'],
        zeroline=False,
        tickfont=dict(color=colors['text'])
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=colors['grid_color'],
        zeroline=False,
        tickfont=dict(color=colors['text'])
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)