from dash import html, dcc
from queries import load_patient_master_list

df_patients = load_patient_master_list()
AVAILABLE_GENDERS = df_patients['gender'].unique().tolist()
AVAILABLE_GLAUCOMA_TYPES = df_patients['type_of_glaucoma'].unique().tolist()
AVAILABLE_NPGS_TYPES = df_patients['npgs_type'].unique().tolist()
# ADDED the two new plots here
AVAILABLE_PLOTS = ['Shift Analysis', 'EWMA IOP', 'GAT vs ARGOS', 'STL Decomposition', 'Visual Field', 'MRW', 'RNFLT'] # Bolinger Bands removed from default selection

def get_login_layout():
    """Generates a modern, native HTML login interface panel."""
    return html.Div(
        style={
            'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 
            'justifyContent': 'center', 'height': '100vh', 'backgroundColor': '#f1f5f9',
            'fontFamily': 'Arial, sans-serif'
        },
        children=[
            html.Div(
                style={
                    'padding': '30px', 'backgroundColor': '#ffffff', 'borderRadius': '8px',
                    'boxShadow': '0 4px 6px -1px rgb(0 0 0 / 0.1)', 'width': '350px'
                },
                children=[
                    html.H2("THEA Dashboard Login", style={'textAlign': 'center', 'color': '#0f172a', 'marginBottom': '20px'}),
                    
                    html.Label("Username", style={'fontWeight': 'bold', 'color': '#334155'}),
                    dcc.Input(id='login-username', type='text', placeholder='Enter username', 
                              style={'width': '100%', 'padding': '0px', 'margin': '8px 0 20px 0', 'borderRadius': '4px', 'border': '1px solid #cbd5e1', 'boxSizing': 'border-box'}),
                    
                    html.Label("Password", style={'fontWeight': 'bold', 'color': '#334155'}),
                    dcc.Input(id='login-password', type='password', placeholder='Enter password', 
                              style={'width': '100%', 'padding': '0px', 'margin': '8px 0 20px 0', 'borderRadius': '4px', 'border': '1px solid #cbd5e1', 'boxSizing': 'border-box'}),
                    
                    html.Button('Sign In', id='login-button', n_clicks=0,
                                style={'width': '100%', 'padding': '12px', 'backgroundColor': '#0369a1', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'fontWeight': 'bold', 'cursor': 'pointer'}),
                    
                    html.Div(id='login-output', style={'marginTop': '15px', 'color': '#ef4444', 'textAlign': 'center', 'fontSize': '14px'})
                ]
            )
        ]
    )

def create_filter_panel(panel_id):
    return html.Div(
        id=f'panel-{panel_id}',
        style={'flex': '1', 'minWidth': '0', 'padding': '10px', 'border': '1px solid #e2e8f0', 'borderRadius': '8px', 'backgroundColor': '#ffffff'},
        children=[
            # --- 1. CONTROLS ---
            html.Div(style={'backgroundColor': '#f8fafc', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '20px'}, children=[
                html.H4(f"View {panel_id} Controls", style={'marginTop': '0', 'color': '#0f172a'}),
                html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '10px', 'fontSize': '14px'}, children=[
                    html.Div([html.Label("Gender:", style={'fontWeight': 'bold'}), dcc.Checklist(id=f'gender-filter-{panel_id}', options=AVAILABLE_GENDERS, value=AVAILABLE_GENDERS, style={'display': 'flex', 'flexDirection': 'column'})]),
                    html.Div([html.Label("Glaucoma:", style={'fontWeight': 'bold'}), dcc.Checklist(id=f'glaucoma-filter-{panel_id}', options=AVAILABLE_GLAUCOMA_TYPES, value=AVAILABLE_GLAUCOMA_TYPES, style={'display': 'flex', 'flexDirection': 'column'})]),
                    html.Div([html.Label("NPGS Type:", style={'fontWeight': 'bold'}), dcc.Checklist(id=f'npgs-filter-{panel_id}', options=AVAILABLE_NPGS_TYPES, value=AVAILABLE_NPGS_TYPES, style={'display': 'flex', 'flexDirection': 'column'})])
                ]),
                html.Hr(),
                html.Label("Select Plots to Display:", style={'fontWeight': 'bold', 'color': '#0369a1'}),
                dcc.Checklist(id=f'plot-selector-{panel_id}', options=[{'label': f" {p}", 'value': p} for p in AVAILABLE_PLOTS], value=['EWMA IOP'], inline=True, style={'marginBottom': '15px', 'display': 'flex', 'gap': '15px', 'flexWrap': 'wrap'}),
                
                html.Div(style={'display': 'flex', 'gap': '20px', 'marginTop': '15px', 'marginBottom': '15px'}, children=[
                    html.Div(style={'flex': '1'}, children=[
                        html.Label("Limit IOP Line:", style={'fontWeight': 'bold', 'color': '#0369a1'}),
                        dcc.Input(id=f'limit-iop-{panel_id}', type='number', value=21, step=1, style={'width': '80px'})
                    ])
                ]),
                
                html.Label("Select Patient:", style={'fontWeight': 'bold', 'color': '#0369a1'}),
                dcc.Dropdown(id=f'patient-dropdown-{panel_id}', placeholder="Select a patient...", style={'marginBottom': '5px'}),
                html.Div(id=f'patient-info-{panel_id}', style={'display': 'none'})
            ]),
            
            # --- 2. PLOT CONTAINERS ---
            html.Div(id=f'container-shift-{panel_id}', style={'display': 'none'}, children=[
                html.Div(style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}, children=[
                    html.Label("Adjust OCT Shift (Days):", style={'fontWeight': 'bold', 'marginRight': '15px', 'color': '#0369a1'}),
                    html.Div(dcc.Slider(id=f'shift-slider-{panel_id}', min=0, max=365, step=5, value=0), style={'flex': '1'})
                ]),
                dcc.Graph(id=f'graph-shift-{panel_id}')
            ]),

            html.Div(id=f'container-ewma-{panel_id}', style={'display': 'none'}, children=[
                html.Div(style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}, children=[
                    html.Label("Adjust EWMA Smoothing (α):", style={'fontWeight': 'bold', 'marginRight': '15px'}),
                    html.Div(dcc.Slider(id=f'alpha-slider-{panel_id}', min=0.1, max=0.99, step=0.05, value=0.3), style={'flex': '1'})
                ]),
                dcc.Graph(id=f'graph-ewma-{panel_id}')
            ]),

            html.Div(id=f'container-gat-argos-{panel_id}', style={'display': 'none'}, children=[
                dcc.Graph(id=f'graph-gat-argos-{panel_id}', style={'marginBottom': '20px'})
            ]),

            # NEW: Bollinger Bands Container
            html.Div(id=f'container-bollinger-{panel_id}', style={'display': 'none'}, children=[
                html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '10px'}, children=[
                    html.Div(style={'flex': '1'}, children=[
                        html.Label("BB Window (Hours):", style={'fontWeight': 'bold'}),
                        dcc.Slider(id=f'bb-window-slider-{panel_id}', min=3, max=48, step=1, value=12)
                    ]),
                    html.Div(style={'flex': '1'}, children=[
                        html.Label("BB Std Dev (k):", style={'fontWeight': 'bold'}),
                        dcc.Slider(id=f'bb-k-slider-{panel_id}', min=1.0, max=3.5, step=0.1, value=2.0)
                    ])
                ]),
                dcc.Graph(id=f'graph-bollinger-{panel_id}')
            ]),

            # NEW: STL Decomposition Container
            html.Div(id=f'container-stl-{panel_id}', style={'display': 'none'}, children=[
                html.Div(style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}, children=[
                    html.Label("STL Period (Hours):", style={'fontWeight': 'bold', 'marginRight': '15px'}),
                    html.Div(dcc.Slider(id=f'stl-period-slider-{panel_id}', min=6, max=48, step=1, value=24), style={'flex': '1'})
                ]),
                dcc.Graph(id=f'graph-stl-{panel_id}')
            ]),

            # Standard Plots
            html.Div(id=f'container-vf-{panel_id}', style={'display': 'none'}, children=[dcc.Graph(id=f'graph-vf-{panel_id}', style={'marginBottom': '20px'})]),
            html.Div(id=f'container-mrw-{panel_id}', style={'display': 'none'}, children=[dcc.Graph(id=f'graph-mrw-{panel_id}', style={'marginBottom': '20px'})]),
            html.Div(id=f'container-rnflt-{panel_id}', style={'display': 'none'}, children=[dcc.Graph(id=f'graph-rnflt-{panel_id}', style={'marginBottom': '20px'})])
        ]
    )

def get_app_layout():
    return html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'maxWidth': '1800px', 'margin': '0 auto', 'backgroundColor': '#f1f5f9'}, children=[
        html.Div(style={'textAlign': 'center', 'marginBottom': '20px'}, children=[
            dcc.RadioItems(id='view-toggle', options=[{'label': ' Single Patient', 'value': 'single'}, {'label': ' Compare Two', 'value': 'split'}], value='single', inline=True)
        ]),
        html.Div(id='main-container', style={'display': 'flex', 'gap': '20px'}, children=[create_filter_panel('1'), create_filter_panel('2')])
    ])