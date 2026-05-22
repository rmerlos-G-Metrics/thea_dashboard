import dash
from dash import Input, Output, html
from layout import get_app_layout, df_patients
from plot_factory import generate_all_figures

app = dash.Dash(__name__)
server = app.server
app.title = "THEA Trophy - Dashboard"

<<<<<<< Updated upstream
def load_patient_master_list():
    conn = sqlite3.connect('THEA.db')
    query = """
    WITH ValidPatients AS (
        SELECT patient_id FROM sulzbach_processed
        UNION
        SELECT patient_id FROM bochum
        UNION
        SELECT patient_id FROM mainz
    )
    SELECT DISTINCT 
        v.patient_id, 
        e.gender, 
        e.type_of_glaucoma,
        e.npgs_type
    FROM ValidPatients v
    LEFT JOIN eyemate_measurements e ON v.patient_id = e.patient_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    df['gender'] = df['gender'].fillna('Unknown')
    df['type_of_glaucoma'] = df['type_of_glaucoma'].fillna('Unknown')
    df['npgs_type'] = df['npgs_type'].fillna('Unknown')
    
    return df

df_patients = load_patient_master_list()

available_genders = df_patients['gender'].unique().tolist()
available_glaucoma_types = df_patients['type_of_glaucoma'].unique().tolist()
available_npgs_types = df_patients['npgs_type'].unique().tolist()

# --- HELPER FUNCTION: Generates a distinct panel based on the ID passed to it ---
def create_filter_panel(panel_id):
    return html.Div(
        id=f'panel-{panel_id}',
        style={'flex': '1', 'minWidth': '0'}, # flex: 1 allows it to share space evenly
        children=[
            # FILTER PANEL
            html.Div(style={'backgroundColor': '#f8fafc', 'padding': '20px', 'borderRadius': '10px', 'border': '1px solid #e2e8f0', 'marginBottom': '20px'}, children=[
                html.H3(f"Filters (View {panel_id})", style={'marginTop': '0', 'color': '#0f172a'}),
                
                # Using 3 columns now since we removed medications
                html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '15px'}, children=[
                    
                    html.Div([
                        html.Label("Gender:", style={'fontWeight': 'bold', 'color': '#475569'}),
                        dcc.Checklist(
                            id=f'gender-filter-{panel_id}',
                            options=[{'label': g, 'value': g} for g in available_genders],
                            value=available_genders, 
                            style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px', 'marginTop': '8px'}
                        )
                    ]),
                    
                    html.Div([
                        html.Label("Glaucoma:", style={'fontWeight': 'bold', 'color': '#475569'}),
                        dcc.Checklist(
                            id=f'glaucoma-filter-{panel_id}',
                            options=[{'label': t, 'value': t} for t in available_glaucoma_types],
                            value=available_glaucoma_types, 
                            style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px', 'marginTop': '8px'}
                        )
                    ]),
                    
                    html.Div([
                        html.Label("NPGS Type:", style={'fontWeight': 'bold', 'color': '#475569'}),
                        dcc.Checklist(
                            id=f'npgs-filter-{panel_id}',
                            options=[{'label': n, 'value': n} for n in available_npgs_types],
                            value=available_npgs_types, 
                            style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px', 'marginTop': '8px'}
                        )
                    ])
                ])
            ]),
            
            # DATA TABLE
            html.Div(children=[
                dash_table.DataTable(
                    id=f'patient-table-{panel_id}',
                    page_size=15, 
                    style_table={'overflowX': 'auto', 'border': '1px solid #e2e8f0'},
                    style_header={'backgroundColor': '#e2e8f0', 'fontWeight': 'bold', 'textAlign': 'left'},
                    style_cell={'padding': '10px', 'textAlign': 'left', 'fontFamily': 'Arial, sans-serif', 'fontSize': '12px'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f8fafc'}]
                )
            ])
        ]
    )


# --- MAIN UI LAYOUT ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'maxWidth': '1600px', 'margin': '0 auto'}, children=[
    html.H1("Patient Filter Validation", style={'textAlign': 'center', 'color': '#333'}),
    
    # The Toggle Control
    html.Div(style={'textAlign': 'center', 'marginBottom': '20px'}, children=[
        dcc.RadioItems(
            id='view-toggle',
            options=[
                {'label': ' Single View', 'value': 'single'},
                {'label': ' Compare Two Patients/Cohorts', 'value': 'split'}
            ],
            value='single', # Default state
            inline=True,
            style={'display': 'inline-flex', 'gap': '20px', 'fontWeight': 'bold', 'padding': '10px 20px', 'backgroundColor': '#e2e8f0', 'borderRadius': '8px'}
        )
    ]),
    
    # The Flex Container holding both panels side-by-side
    html.Div(
        id='main-container', 
        style={'display': 'flex', 'gap': '30px'}, 
        children=[
            create_filter_panel('1'), # Always visible
            create_filter_panel('2')  # Hidden by default, shown when 'Compare' is clicked
        ]
    )
])

# --- CALLBACK 1: Handle the Split View Toggle ---
@app.callback(
    Output('panel-2', 'style'),
    Input('view-toggle', 'value')
)
def toggle_split_view(view_mode):
    if view_mode == 'single':
        return {'display': 'none'} # Hides panel 2 entirely
    else:
        return {'flex': '1', 'minWidth': '0', 'display': 'block'} # Restores panel 2

# --- DATA FILTERING LOGIC (Helper function used by both callbacks) ---
def filter_dataframe(genders, glaucomas, npgs):
    dff = df_patients.copy()
    empty_data = []
    columns = [{"name": i, "id": i} for i in dff.columns]
    
    if not genders or not glaucomas or not npgs:
        return empty_data, columns
        
    dff = dff[dff['gender'].isin(genders)]
    dff = dff[dff['type_of_glaucoma'].isin(glaucomas)]
    dff = dff[dff['npgs_type'].isin(npgs)]
    
    return dff.to_dict('records'), columns

# --- CALLBACK 2: Update View 1 ---
@app.callback(
    [Output('patient-table-1', 'data'),
     Output('patient-table-1', 'columns')],
    [Input('gender-filter-1', 'value'),
     Input('glaucoma-filter-1', 'value'),
     Input('npgs-filter-1', 'value')]
)
def update_table_1(selected_genders, selected_glaucoma, selected_npgs):
    return filter_dataframe(selected_genders, selected_glaucoma, selected_npgs)

# --- CALLBACK 3: Update View 2 ---
@app.callback(
    [Output('patient-table-2', 'data'),
     Output('patient-table-2', 'columns')],
    [Input('gender-filter-2', 'value'),
     Input('glaucoma-filter-2', 'value'),
     Input('npgs-filter-2', 'value')]
)
def update_table_2(selected_genders, selected_glaucoma, selected_npgs):
    return filter_dataframe(selected_genders, selected_glaucoma, selected_npgs)
=======
app.layout = get_app_layout()

# --- View Toggle & Patient Info Callbacks ---
@app.callback(Output('panel-2', 'style'), Input('view-toggle', 'value'))
def toggle_split_view(view_mode):
    return {'display': 'none'} if view_mode == 'single' else {'flex': '1', 'minWidth': '0', 'display': 'block'}

def update_dropdown_options(genders, glaucomas, npgs):
    if not genders or not glaucomas or not npgs: return []
    dff = df_patients[df_patients['gender'].isin(genders) & df_patients['type_of_glaucoma'].isin(glaucomas) & df_patients['npgs_type'].isin(npgs)]
    return [{'label': p, 'value': p} for p in dff['patient_id'].unique()]

@app.callback(Output('patient-dropdown-1', 'options'), [Input('gender-filter-1', 'value'), Input('glaucoma-filter-1', 'value'), Input('npgs-filter-1', 'value')])
def update_dd_1(g, gl, n): return update_dropdown_options(g, gl, n)

@app.callback(Output('patient-dropdown-2', 'options'), [Input('gender-filter-2', 'value'), Input('glaucoma-filter-2', 'value'), Input('npgs-filter-2', 'value')])
def update_dd_2(g, gl, n): return update_dropdown_options(g, gl, n)

def build_patient_info_box(patient_id):
    if not patient_id: return "", {'display': 'none'}
    row = df_patients[df_patients['patient_id'] == patient_id].iloc[0]
    content = html.Div([
        html.Strong("Glaucoma Type: ", style={'color': '#0369a1'}), html.Span(row['type_of_glaucoma']), html.Br(),
        html.Strong("NPGS Type: ", style={'color': '#0369a1'}), html.Span(row['npgs_type']), html.Br(),
        html.Strong("Gender: ", style={'color': '#0369a1'}), html.Span(row['gender'])
    ])
    style = {'marginTop': '10px', 'padding': '12px', 'backgroundColor': '#e0f2fe', 'borderRadius': '5px', 'border': '1px solid #bae6fd', 'display': 'block', 'fontSize': '13px'}
    return content, style

@app.callback([Output('patient-info-1', 'children'), Output('patient-info-1', 'style')], Input('patient-dropdown-1', 'value'))
def update_info_1(patient_id): return build_patient_info_box(patient_id)

@app.callback([Output('patient-info-2', 'children'), Output('patient-info-2', 'style')], Input('patient-dropdown-2', 'value'))
def update_info_2(patient_id): return build_patient_info_box(patient_id)


# --- NEW: Container Visibility Toggle ---
def toggle_plot_containers(selected_plots):
    if not selected_plots: selected_plots = []
    
    # Define styles: show if checked, hide if not
    s_shift = {'display': 'block', 'border': '1px solid #bae6fd', 'backgroundColor': '#f0f9ff', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '20px'} if 'Shift Analysis' in selected_plots else {'display': 'none'}
    s_ewma = {'display': 'block', 'border': '1px solid #e2e8f0', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '20px'} if 'EWMA IOP' in selected_plots else {'display': 'none'}
    s_vf = {'display': 'block'} if 'Visual Field' in selected_plots else {'display': 'none'}
    s_mrw = {'display': 'block'} if 'MRW' in selected_plots else {'display': 'none'}
    s_rnflt = {'display': 'block'} if 'RNFLT' in selected_plots else {'display': 'none'}
    
    return s_shift, s_ewma, s_vf, s_mrw, s_rnflt

@app.callback(
    [Output('container-shift-1', 'style'), Output('container-ewma-1', 'style'), Output('container-vf-1', 'style'), Output('container-mrw-1', 'style'), Output('container-rnflt-1', 'style')],
    Input('plot-selector-1', 'value')
)
def toggle_view_1(plots): return toggle_plot_containers(plots)

@app.callback(
    [Output('container-shift-2', 'style'), Output('container-ewma-2', 'style'), Output('container-vf-2', 'style'), Output('container-mrw-2', 'style'), Output('container-rnflt-2', 'style')],
    Input('plot-selector-2', 'value')
)
def toggle_view_2(plots): return toggle_plot_containers(plots)


# --- Update Graph Figures ---
@app.callback(
    [Output('graph-shift-1', 'figure'), Output('graph-ewma-1', 'figure'), Output('graph-vf-1', 'figure'), Output('graph-mrw-1', 'figure'), Output('graph-rnflt-1', 'figure')],
    [Input('patient-dropdown-1', 'value'), Input('alpha-slider-1', 'value'), Input('shift-slider-1', 'value')]
)
def update_figs_1(p, a, s): return generate_all_figures(p, a, s)

@app.callback(
    [Output('graph-shift-2', 'figure'), Output('graph-ewma-2', 'figure'), Output('graph-vf-2', 'figure'), Output('graph-mrw-2', 'figure'), Output('graph-rnflt-2', 'figure')],
    [Input('patient-dropdown-2', 'value'), Input('alpha-slider-2', 'value'), Input('shift-slider-2', 'value')]
)
def update_figs_2(p, a, s): return generate_all_figures(p, a, s)
>>>>>>> Stashed changes

if __name__ == '__main__':
    app.run(debug=True)