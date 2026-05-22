import dash
from dash import Input, Output, html
from layout import get_app_layout, df_patients
from plot_factory import generate_all_figures

app = dash.Dash(__name__)
server = app.server
app.title = "THEA Trophy - Dashboard"

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

if __name__ == '__main__':
    app.run(debug=True)