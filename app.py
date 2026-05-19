import dash
from dash import html, Input, Output, dcc
import pandas as pd
import sqlite3

app = dash.Dash(__name__)

server = app.server

def get_patient_list():
    conn = sqlite3.connect('THEA.db')
    query = "SELECT DISTINCT patient_id FROM sulzbach_processed"
    patients_df = pd.read_sql(query, conn)
    conn.close()
    return patients_df['patient_id'].tolist()

patients = get_patient_list()

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
    html.H1("Sulzbach Dashboard", style={'textAlign': 'center', 'color': '#333'}),
    html.Label("Select Patient:", style={'fontSize': '18px', 'marginBottom': '10px'}),
    dcc.Dropdown(
        id='patient-dropdown',
        options=[{'label': p, 'value': p} for p in patients],
        value=patients[0] if patients else None, # Default to the first patient
        style={'width': '300px', 'marginBottom': '20px'}
    ),
    
    html.Hr(),
    
    html.Div(id='data-output')
])

@app.callback(
    Output('data-output', 'children'),
    Input('patient-dropdown', 'value')
)

def update_dashboard(selected_patient):
    if not selected_patient:
        return "Please select a patient."
    
    conn = sqlite3.connect('THEA.db')
    
    query = "SELECT * FROM eyemate_measurements WHERE patient_id = ?"
    df = pd.read_sql(query, conn, params=(selected_patient,))
    conn.close()
    
    return html.Div([
        html.H3(f"Recent data for {selected_patient}:"),
        html.Pre(df.head().to_string())
    ])


if __name__ == '__main__':
    app.run_server(debug=True)

