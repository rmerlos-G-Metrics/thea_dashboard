import dash
from dash import html, Input, Output, dcc
from dash import dash_table
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = dash.Dash(__name__)
server = app.server
app.title = "THEA Trophy - Dashboard"

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

if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run(debug=True)
