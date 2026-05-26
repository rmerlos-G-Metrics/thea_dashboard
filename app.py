import dash
from dash import Input, Output, html
from layout import get_app_layout, df_patients
from plot_factory import generate_all_figures

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "THEA Trophy - Dashboard"

app.layout = get_app_layout()

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

# --- Container Visibility Toggle (Now maps 7 containers) ---
def toggle_plot_containers(selected_plots):
    if not selected_plots: selected_plots = []
    
    # Generic show/hide styles
    block_style = {'display': 'block', 'border': '1px solid #e2e8f0', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '20px'}
    hide_style = {'display': 'none'}
    
    s_shift = {'display': 'block', 'border': '1px solid #bae6fd', 'backgroundColor': '#f0f9ff', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '20px'} if 'Shift Analysis' in selected_plots else hide_style
    s_ewma = block_style if 'EWMA IOP' in selected_plots else hide_style
    s_boll = block_style if 'Bollinger Bands' in selected_plots else hide_style
    s_stl = block_style if 'STL Decomposition' in selected_plots else hide_style
    s_vf = {'display': 'block'} if 'Visual Field' in selected_plots else hide_style
    s_mrw = {'display': 'block'} if 'MRW' in selected_plots else hide_style
    s_rnflt = {'display': 'block'} if 'RNFLT' in selected_plots else hide_style
    s_gat_argos = {'display': 'block'} if 'GAT vs ARGOS' in selected_plots else hide_style
    
    return s_shift, s_ewma, s_boll, s_stl, s_vf, s_mrw, s_rnflt, s_gat_argos

@app.callback(
    [Output('container-shift-1', 'style'), Output('container-ewma-1', 'style'), Output('container-bollinger-1', 'style'), Output('container-stl-1', 'style'), Output('container-vf-1', 'style'), Output('container-mrw-1', 'style'), Output('container-rnflt-1', 'style'), Output('container-gat-argos-1', 'style')],
    Input('plot-selector-1', 'value')
)
def toggle_view_1(plots): return toggle_plot_containers(plots)

@app.callback(
    [Output('container-shift-2', 'style'), Output('container-ewma-2', 'style'), Output('container-bollinger-2', 'style'), Output('container-stl-2', 'style'), Output('container-vf-2', 'style'), Output('container-mrw-2', 'style'), Output('container-rnflt-2', 'style'), Output('container-gat-argos-2', 'style')],
    Input('plot-selector-2', 'value')
)
def toggle_view_2(plots): return toggle_plot_containers(plots)

# --- Graph Figures (Now mapping 7 outputs and the new slider inputs) ---
@app.callback(
    [Output('graph-shift-1', 'figure'), Output('graph-ewma-1', 'figure'), Output('graph-bollinger-1', 'figure'), Output('graph-stl-1', 'figure'), Output('graph-vf-1', 'figure'), Output('graph-mrw-1', 'figure'), Output('graph-rnflt-1', 'figure'), Output('graph-gat-argos-1', 'figure')],
    [Input('patient-dropdown-1', 'value'), Input('alpha-slider-1', 'value'), Input('shift-slider-1', 'value'), Input('bb-window-slider-1', 'value'), Input('bb-k-slider-1', 'value'), Input('stl-period-slider-1', 'value'), Input('plot-selector-1', 'value'), Input('limit-iop-1', 'value')]
)
def update_figs_1(p, a, s, bbw, bbk, stlp, plots, limit_iop): return generate_all_figures(p, a, s, bbw, bbk, stlp, plots, limit_iop)

@app.callback(
    [Output('graph-shift-2', 'figure'), Output('graph-ewma-2', 'figure'), Output('graph-bollinger-2', 'figure'), Output('graph-stl-2', 'figure'), Output('graph-vf-2', 'figure'), Output('graph-mrw-2', 'figure'), Output('graph-rnflt-2', 'figure'), Output('graph-gat-argos-2', 'figure')],
    [Input('patient-dropdown-2', 'value'), Input('alpha-slider-2', 'value'), Input('shift-slider-2', 'value'), Input('bb-window-slider-2', 'value'), Input('bb-k-slider-2', 'value'), Input('stl-period-slider-2', 'value'), Input('plot-selector-2', 'value'), Input('limit-iop-2', 'value')]
)
def update_figs_2(p, a, s, bbw, bbk, stlp, plots, limit_iop): return generate_all_figures(p, a, s, bbw, bbk, stlp, plots, limit_iop)

if __name__ == '__main__':
    app.run(debug=True)