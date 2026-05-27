import os
import dash
from dash import Input, Output, State, html, dcc
from flask import Flask, session
from layout import get_app_layout, get_login_layout, df_patients
from plot_factory import generate_all_figures
from dotenv import load_dotenv

load_dotenv()

server = Flask(__name__)
server.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-engineering-key-2026")

app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)
app.title = "THEA Trophy - Dashboard"

USERNAME = os.environ.get("APP_USERNAME")
PASSWORD = os.environ.get("PASSWORD")

app.layout = html.Div([dcc.Location(id='url', refresh=False), html.Div(id='page-content')])

@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if session.get('authenticated'): return get_app_layout()
    return get_login_layout()

@app.callback(
    [Output('url', 'pathname'), Output('login-output', 'children')],
    Input('login-button', 'n_clicks'),
    [State('login-username', 'value'), State('login-password', 'value')],
    prevent_initial_call=True
)
def login_auth(n_clicks, username, password):
    if n_clicks > 0:
        if username == USERNAME and password == PASSWORD:
            session['authenticated'] = True 
            return '/', ''
        else: return dash.no_update, 'Invalid username or password.'
    return dash.no_update, ''

@app.callback(Output('panel-2', 'style'), Input('view-toggle', 'value'))
def toggle_split_view(view_mode): return {'display': 'none'} if view_mode == 'single' else {'flex': '1', 'minWidth': '0', 'display': 'block'}

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


def toggle_plot_containers(selected_plots, stl_components):
    if not selected_plots: selected_plots = []
    if not stl_components: stl_components = []
    
    block_style = {'display': 'block', 'border': '1px solid #e2e8f0', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '20px'}
    hide_style = {'display': 'none'}
    
    s_ewma = block_style if 'EWMA IOP' in selected_plots else hide_style
    s_vf = {'display': 'block'} if 'Visual Field' in selected_plots else hide_style
    
    stl_active = 'STL Decomposition' in selected_plots
    s_stl_trend = block_style if stl_active and 'Trend' in stl_components else hide_style
    s_stl_seasonal = block_style if stl_active and 'Seasonal' in stl_components else hide_style
    s_stl_resid = block_style if stl_active and 'Residuals' in stl_components else hide_style
    
    # Hide/show STL sub-controls
    s_stl_controls = {'display': 'block'} if stl_active else hide_style

    return s_ewma, s_stl_trend, s_stl_seasonal, s_stl_resid, s_vf, s_stl_controls

@app.callback(
    [Output('container-ewma-1', 'style'), Output('container-stl-trend-1', 'style'), Output('container-stl-seasonal-1', 'style'), Output('container-stl-resid-1', 'style'), Output('container-vf-1', 'style'), Output('stl-controls-1', 'style')],
    [Input('plot-selector-1', 'value'), Input('stl-selector-1', 'value')]
)
def toggle_view_1(plots, stl): return toggle_plot_containers(plots, stl)

@app.callback(
    [Output('container-ewma-2', 'style'), Output('container-stl-trend-2', 'style'), Output('container-stl-seasonal-2', 'style'), Output('container-stl-resid-2', 'style'), Output('container-vf-2', 'style'), Output('stl-controls-2', 'style')],
    [Input('plot-selector-2', 'value'), Input('stl-selector-2', 'value')]
)
def toggle_view_2(plots, stl): return toggle_plot_containers(plots, stl)


@app.callback(
    [Output('graph-ewma-1', 'figure'), Output('graph-stl-trend-1', 'figure'), Output('graph-stl-seasonal-1', 'figure'), Output('graph-stl-resid-1', 'figure'), Output('graph-vf-1', 'figure')],
    [Input('patient-dropdown-1', 'value'), Input('alpha-slider-1', 'value'), Input('mrw-shift-slider-1', 'value'), Input('rnflt-shift-slider-1', 'value'), Input('stl-period-slider-1', 'value'), Input('plot-selector-1', 'value'), Input('stl-selector-1', 'value'), Input('overlay-selector-1', 'value'), Input('limit-iop-1', 'value')]
)
def update_figs_1(p, a, mrw_s, rnflt_s, stlp, plots, stl_c, overlays, limit): 
    return generate_all_figures(p, a, mrw_s, rnflt_s, stlp, plots, stl_c, overlays, limit)

@app.callback(
    [Output('graph-ewma-2', 'figure'), Output('graph-stl-trend-2', 'figure'), Output('graph-stl-seasonal-2', 'figure'), Output('graph-stl-resid-2', 'figure'), Output('graph-vf-2', 'figure')],
    [Input('patient-dropdown-2', 'value'), Input('alpha-slider-2', 'value'), Input('mrw-shift-slider-2', 'value'), Input('rnflt-shift-slider-2', 'value'), Input('stl-period-slider-2', 'value'), Input('plot-selector-2', 'value'), Input('stl-selector-2', 'value'), Input('overlay-selector-2', 'value'), Input('limit-iop-2', 'value')]
)
def update_figs_2(p, a, mrw_s, rnflt_s, stlp, plots, stl_c, overlays, limit): 
    return generate_all_figures(p, a, mrw_s, rnflt_s, stlp, plots, stl_c, overlays, limit)

if __name__ == '__main__':
    app.run(debug=True)