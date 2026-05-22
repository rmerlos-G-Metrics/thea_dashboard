import dash
from dash import html, Input, Output, dcc
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from plotly.subplots import make_subplots # <-- NEW IMPORT for Dual Axes

app = dash.Dash(__name__)
server = app.server

def get_patient_list():
    conn = sqlite3.connect('THEA.db')
    query = "SELECT DISTINCT patient_id FROM sulzbach_processed"
    patients_df = pd.read_sql(query, conn)
    conn.close()
    return patients_df['patient_id'].tolist()

patients = get_patient_list()

app.title = "THEA Trophy - Dashboard"

# --- UI LAYOUT ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'maxWidth': '1200px', 'margin': '0 auto'}, children=[
    html.H1("THEA Trophy", style={'textAlign': 'center', 'color': '#333'}),
    
    # MAIN Control Panel
    html.Div(style={'display': 'flex', 'gap': '40px', 'alignItems': 'center', 'backgroundColor': '#f8fafc', 'padding': '20px', 'borderRadius': '10px', 'border': '1px solid #e2e8f0'}, children=[
        html.Div(style={'flex': '1'}, children=[
            html.Label("Patient:", style={'fontWeight': 'bold', 'color': '#475569'}),
            dcc.Dropdown(
                id='patient-dropdown',
                options=[{'label': p, 'value': p} for p in patients],
                value=patients[0] if patients else None,
                style={'marginTop': '8px'}
            )
        ]),
        html.Div(style={'flex': '2'}, children=[
            html.Label("EWMA Smoothing Factor (α):", style={'fontWeight': 'bold', 'color': '#475569'}),
            dcc.Slider(
                id='alpha-slider', min=0.1, max=0.99, step=0.05, value=0.3,
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ])
    ]),
    
    html.Hr(style={'margin': '30px 0'}),
    
    html.Div(style={'backgroundColor': '#e0f2fe', 'padding': '20px', 'borderRadius': '10px', 'border': '1px solid #bae6fd', 'marginBottom': '30px'}, children=[
        html.H3("IOP Shift Analysis", style={'marginTop': '0', 'color': '#0369a1'}),
        html.Label("Shift by Days", style={'fontSize': '14px', 'color': '#0c4a6e'}),
        # Slider allows sliding backward or forward up to a year
        dcc.Slider(
            id='shift-slider', min=0, max=365, step=5, value=0,
            marks={0: 'No Shift', 180: '+6 Mo', 365: '+1 Year'},
            tooltip={"placement": "bottom", "always_visible": True}
        ),
        dcc.Graph(id='shift-graph')
    ]),

    # Graph 1: Eyemate Pressure
    dcc.Graph(id='ewma-graph'),
    
    # Grid Layout for the 3 Standard OCT/Visual Field Graphs
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr', 'gap': '20px', 'marginTop': '20px'}, children=[
        dcc.Graph(id='vf-graph'),
        dcc.Graph(id='mrw-graph'),
        dcc.Graph(id='rnfl-graph')
    ])
])


# --- CALLBACK 1: The New Time-Shift Graph ---
@app.callback(
    Output('shift-graph', 'figure'),
    [Input('patient-dropdown', 'value'),
     Input('alpha-slider', 'value'),
     Input('shift-slider', 'value')]
)
def update_shift_graph(selected_patient, alpha, shift_days):
    if not selected_patient:
        return go.Figure().update_layout(template="plotly_white")
        
    conn = sqlite3.connect('THEA.db')
    
    # 1. Get IOP Data
    df_eye = pd.read_sql("SELECT time_of_measurement, eye_pressure FROM eyemate_measurements WHERE patient_id = ?", conn, params=(selected_patient,))
    
    # 2. Get OCT Data
    df_oct = pd.read_sql("SELECT date, mrw_g, rnfl_g FROM sulzbach_processed WHERE patient_id = ?", conn, params=(selected_patient,))
    conn.close()

    # Create figure with DUAL Y-AXES
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    if not df_eye.empty:
        df_eye['time_of_measurement'] = pd.to_datetime(df_eye['time_of_measurement'], errors='coerce')
        df_eye['eye_pressure'] = pd.to_numeric(df_eye['eye_pressure'], errors='coerce')
        df_eye = df_eye.dropna().sort_values('time_of_measurement')
        
        # Calculate EWMA
        df_eye['ewma'] = df_eye['eye_pressure'].ewm(alpha=alpha, adjust=False).mean()
        
        # Plot ONLY the EWMA line on the Primary Y-Axis (Left)
        fig.add_trace(go.Scatter(
            x=df_eye['time_of_measurement'], y=df_eye['ewma'], 
            mode='lines', line=dict(color='#ef4444', width=3), name=f'IOP EWMA (α={alpha})'
        ), secondary_y=False)

    if not df_oct.empty:
        df_oct['date'] = pd.to_datetime(df_oct['date'], errors='coerce')
        
        # Apply the time shift!
        # If shift_days is 30, we add 30 days to the OCT dates, moving them visually to the right
        df_oct['shifted_date'] = df_oct['date'] + pd.to_timedelta(shift_days, unit='d')
        df_oct = df_oct.sort_values('shifted_date')

        # Clean comma decimals for OCT
        for col in ['mrw_g', 'rnfl_g']:
            if df_oct[col].dtype == 'object':
                df_oct[col] = df_oct[col].astype(str).str.replace(',', '.')
            df_oct[col] = pd.to_numeric(df_oct[col], errors='coerce')

        # Plot MRW on Secondary Y-Axis (Right)
        fig.add_trace(go.Scatter(
            x=df_oct['shifted_date'], y=df_oct['mrw_g'], 
            mode='lines+markers', line=dict(color='#0ea5e9'), name='Global MRW'
        ), secondary_y=True)

        # Plot RNFL on Secondary Y-Axis (Right)
        fig.add_trace(go.Scatter(
            x=df_oct['shifted_date'], y=df_oct['rnfl_g'], 
            mode='lines+markers', line=dict(color='#8b5cf6'), name='Global RNFLT'
        ), secondary_y=True)

    fig.update_layout(
        title=f"Shifted by {shift_days} days",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Set axis titles
    fig.update_yaxes(title_text="<b>IOP</b> (mmHg)", secondary_y=False)
    fig.update_yaxes(title_text="<b>OCT Thickness</b> (μm)", secondary_y=True)

    return fig

# --- CALLBACK 2: The Original 4 Graphs ---
# (This remains exactly the same as the previous code block, handling ewma, vf, mrw, and rnfl graphs)
@app.callback(
    [Output('ewma-graph', 'figure'),
     Output('vf-graph', 'figure'),
     Output('mrw-graph', 'figure'),
     Output('rnfl-graph', 'figure')],
    [Input('patient-dropdown', 'value'),
     Input('alpha-slider', 'value')]
)
def update_standard_graphs(selected_patient, alpha):
    # Fallback empty figures
    empty_fig = go.Figure().update_layout(template="plotly_white")
    if not selected_patient:
        return empty_fig.update_layout(title="Select a patient"), empty_fig, empty_fig, empty_fig
    
    conn = sqlite3.connect('THEA.db')
    
    # 1. EWMA Graph
    df_eye = pd.read_sql("SELECT time_of_measurement, eye_pressure FROM eyemate_measurements WHERE patient_id = ?", conn, params=(selected_patient,))
    fig_ewma = go.Figure()
    if not df_eye.empty:
        df_eye['time_of_measurement'] = pd.to_datetime(df_eye['time_of_measurement'], errors='coerce')
        df_eye['eye_pressure'] = pd.to_numeric(df_eye['eye_pressure'], errors='coerce')
        df_eye = df_eye.dropna().sort_values('time_of_measurement')
        df_eye['ewma'] = df_eye['eye_pressure'].ewm(alpha=alpha, adjust=False).mean()
        
        fig_ewma.add_trace(go.Scatter(x=df_eye['time_of_measurement'], y=df_eye['eye_pressure'], mode='markers', marker=dict(color='rgba(59, 130, 246, 0.3)'), name='Raw'))
        fig_ewma.add_trace(go.Scatter(x=df_eye['time_of_measurement'], y=df_eye['ewma'], mode='lines', line=dict(color="#1e750d", width=2.5), name=f'EWMA (α={alpha})'))
        fig_ewma.add_hline(y=18, line_dash="dash", line_color="red", annotation_text="Target: 18")
    fig_ewma.update_layout(title="IOP", hovermode="x unified", template="plotly_white")

    # 2. OCT/VF Graphs
    df_oct = pd.read_sql("SELECT * FROM sulzbach_processed WHERE patient_id = ?", conn, params=(selected_patient,))
    conn.close()

    def build_category_fig(df, columns, title, y_label):
        fig = go.Figure()
        if df.empty: return fig.update_layout(title=f"No data for {title}")
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date')

        for col in columns:
            if col in df.columns:
                if df[col].dtype == 'object': df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
                fig.add_trace(go.Scatter(x=df['date'], y=df[col], mode='lines+markers', name=col.upper(), connectgaps=True))
        
        fig.update_layout(title=title, yaxis_title=y_label, hovermode="x unified", template="plotly_white", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        return fig

    vf_cols = ['ms_db', 'md_db', 'slv_db']
    mrw_cols = ['mrw_ti', 'mrw_t', 'mrw_ts', 'mrw_ns', 'mrw_n', 'mrw_ni', 'mrw_gc', 'mrw_g']
    rnfl_cols = ['rnfl_ti', 'rnfl_t', 'rnfl_ts', 'rnfl_ns', 'rnfl_n', 'rnfl_ni', 'rnfl_gc', 'rnfl_g']

    fig_vf = build_category_fig(df_oct, vf_cols, "Visual Field Parameters", "dB")
    fig_mrw = build_category_fig(df_oct, mrw_cols, "Minimum Rim Width (MRW)", "μm")
    fig_rnfl = build_category_fig(df_oct, rnfl_cols, "Retinal Nerve Fiber Layer (RNFLT)", "μm")

    return fig_ewma, fig_vf, fig_mrw, fig_rnfl

if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run(debug=True)
