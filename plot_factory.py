import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from queries import get_patient_data

def build_category_fig(df, columns, title, y_label):
    fig = go.Figure()
    if df.empty: return fig.update_layout(title=f"No data for {title}", template="plotly_white")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values('date')
    for col in columns:
        if col in df.columns:
            if df[col].dtype == 'object': df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            fig.add_trace(go.Scatter(x=df['date'], y=df[col], mode='lines+markers', name=col.upper(), connectgaps=True))
    fig.update_layout(title=title, yaxis_title=y_label, hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
    return fig

def generate_all_figures(selected_patient, alpha, shift_days):
    """Calculates all figures. If no patient is selected, returns empty figures."""
    empty_fig = go.Figure().update_layout(template="plotly_white", title="Select a patient to view data")
    if not selected_patient:
        return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    alpha = alpha if alpha is not None else 0.3
    shift_days = shift_days if shift_days is not None else 0

    df_eye, df_oct = get_patient_data(selected_patient)

    if not df_eye.empty:
        df_eye['time_of_measurement'] = pd.to_datetime(df_eye['time_of_measurement'], errors='coerce')
        df_eye['eye_pressure'] = pd.to_numeric(df_eye['eye_pressure'], errors='coerce')
        df_eye = df_eye.dropna().sort_values('time_of_measurement')
        df_eye['ewma'] = df_eye['eye_pressure'].ewm(alpha=alpha, adjust=False).mean()

    # 1. Shift Graph
    fig_shift = make_subplots(specs=[[{"secondary_y": True}]])
    if not df_eye.empty:
        fig_shift.add_trace(go.Scatter(x=df_eye['time_of_measurement'], y=df_eye['ewma'], mode='lines', line=dict(color='#ef4444', width=3), name='IOP EWMA'), secondary_y=False)
    if not df_oct.empty:
        df_oct['date'] = pd.to_datetime(df_oct['date'], errors='coerce')
        df_oct['shifted_date'] = df_oct['date'] + pd.to_timedelta(shift_days, unit='d')
        df_oct = df_oct.sort_values('shifted_date')
        for col in ['mrw_g', 'rnfl_g']:
            if df_oct[col].dtype == 'object': df_oct[col] = df_oct[col].astype(str).str.replace(',', '.')
            df_oct[col] = pd.to_numeric(df_oct[col], errors='coerce')
        fig_shift.add_trace(go.Scatter(x=df_oct['shifted_date'], y=df_oct['mrw_g'], mode='lines+markers', line=dict(color='#0ea5e9'), name='Global MRW'), secondary_y=True)
        fig_shift.add_trace(go.Scatter(x=df_oct['shifted_date'], y=df_oct['rnfl_g'], mode='lines+markers', line=dict(color='#8b5cf6'), name='Global RNFLT'), secondary_y=True)
    fig_shift.update_layout(title=f"Shifted by {shift_days} days", hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))

    # 2. EWMA Graph
    fig_ewma = go.Figure()
    if not df_eye.empty:
        fig_ewma.add_trace(go.Scatter(x=df_eye['time_of_measurement'], y=df_eye['eye_pressure'], mode='markers', marker=dict(color='rgba(59, 130, 246, 0.3)'), name='Raw'))
        fig_ewma.add_trace(go.Scatter(x=df_eye['time_of_measurement'], y=df_eye['ewma'], mode='lines', line=dict(color="#1e750d", width=2.5), name='EWMA'))
        fig_ewma.add_hline(y=18, line_dash="dash", line_color="red", annotation_text="Target: 18")
    fig_ewma.update_layout(title="IOP & EWMA", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))

    # 3, 4, 5. Standard Graphs
    fig_vf = build_category_fig(df_oct, ['ms_db', 'md_db', 'slv_db'], "Visual Field", "dB")
    fig_mrw = build_category_fig(df_oct, ['mrw_ti', 'mrw_t', 'mrw_ts', 'mrw_ns', 'mrw_n', 'mrw_ni', 'mrw_gc', 'mrw_g'], "MRW", "μm")
    fig_rnflt = build_category_fig(df_oct, ['rnfl_ti', 'rnfl_t', 'rnfl_ts', 'rnfl_ns', 'rnfl_n', 'rnfl_ni', 'rnfl_gc', 'rnfl_g'], "RNFLT", "μm")

    return fig_shift, fig_ewma, fig_vf, fig_mrw, fig_rnflt