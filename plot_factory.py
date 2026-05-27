import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import STL 
from queries import get_patient_data, get_visit_data

def apply_system_overlays(fig, limit_iop):
    if limit_iop is not None:
        fig.add_hline(
            y=limit_iop, line_dash="dash", line_color="red", layer="below", 
            annotation_text=f"Limit: {limit_iop}mmHg", annotation_position="top right"
        )
    return fig

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

def add_global_overlays(fig, df_visits, df_oct, mrw_shift, rnfl_shift, overlays):
    """Helper to inject GAT, ARGOS, MRW, and rnfl into any plot using a secondary y-axis if needed."""
    
    # 1. Primary Y-Axis Overlays (IOP based)
    if not df_visits.empty:
        viz_gat = True if 'GAT' in overlays else 'legendonly'
        if 'gat_mean' in df_visits.columns:
            fig.add_trace(go.Scatter(x=df_visits['date'], y=df_visits['gat_mean'], mode='lines+markers', name='GAT', marker=dict(symbol='square', size=8), line=dict(color='#cf6b3a', width=2, dash='dot'), connectgaps=True, visible=viz_gat), secondary_y=False)
            
        viz_argos = True if 'ARGOS' in overlays else 'legendonly'
        if 'argos_mean' in df_visits.columns:
            fig.add_trace(go.Scatter(x=df_visits['date'], y=df_visits['argos_mean'], mode='lines+markers', name='ARGOS', marker=dict(symbol='circle', size=8), line=dict(color='#8b5cf6', width=2, dash='dot'), connectgaps=True, visible=viz_argos), secondary_y=False)
            
    # 2. Secondary Y-Axis Overlays (OCT based - µm)
    if not df_oct.empty:
        viz_mrw = True if 'MRW' in overlays else 'legendonly'
        if 'mrw_g' in df_oct.columns:
            mrw_dates = pd.to_datetime(df_oct['date'], errors='coerce') + pd.to_timedelta(mrw_shift, unit='d')
            fig.add_trace(go.Scatter(x=mrw_dates, y=df_oct['mrw_g'], mode='lines+markers', name=f'MRW Global (Shift: {mrw_shift}d)', marker=dict(symbol='diamond'), line=dict(color='#0ea5e9', dash='longdash'), connectgaps=True, visible=viz_mrw), secondary_y=True)

        viz_rnfl = True if 'rnfl' in overlays else 'legendonly'
        if 'rnfl_g' in df_oct.columns:
            rnfl_dates = pd.to_datetime(df_oct['date'], errors='coerce') + pd.to_timedelta(rnfl_shift, unit='d')
            fig.add_trace(go.Scatter(x=rnfl_dates, y=df_oct['rnfl_g'], mode='lines+markers', name=f'rnfl Global (Shift: {rnfl_shift}d)', marker=dict(symbol='triangle-up'), line=dict(color='#ec4899', dash='longdash'), connectgaps=True, visible=viz_rnfl), secondary_y=True)
            
    return fig

def generate_all_figures(selected_patient, alpha, mrw_shift, rnfl_shift, stl_period, selected_plots, stl_components, global_overlays, limit_iop):
    empty_fig = go.Figure().update_layout(template="plotly_white", title="Select a patient to view data")
    
    if not selected_patient or not selected_plots:
        return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    # Safe defaults
    alpha = alpha if alpha is not None else 0.3
    mrw_shift = mrw_shift if mrw_shift is not None else 0
    rnfl_shift = rnfl_shift if rnfl_shift is not None else 0
    stl_period = stl_period if stl_period is not None else 24
    if not global_overlays: global_overlays = []
    if not stl_components: stl_components = []

    # --- 1. DATA PREP & RESAMPLING ---
    df_eye, df_oct = get_patient_data(selected_patient)
    df_visits = get_visit_data(selected_patient)
    
    if not df_visits.empty:
        df_visits['date'] = pd.to_datetime(df_visits['date'], errors='coerce')
        for col in ['gat_mean', 'argos_mean']:
            if col in df_visits.columns:
                if df_visits[col].dtype == 'object': df_visits[col] = df_visits[col].astype(str).str.replace(',', '.')
                df_visits[col] = pd.to_numeric(df_visits[col], errors='coerce')
        df_visits = df_visits.sort_values('date')

    if not df_oct.empty:
        for col in ['mrw_g', 'rnfl_g']:
            if df_oct[col].dtype == 'object': df_oct[col] = df_oct[col].astype(str).str.replace(',', '.')
            df_oct[col] = pd.to_numeric(df_oct[col], errors='coerce')

    resampled = pd.Series(dtype=float)
    if not df_eye.empty:
        df_eye['time_of_measurement'] = pd.to_datetime(df_eye['time_of_measurement'], errors='coerce')
        df_eye['eye_pressure'] = pd.to_numeric(df_eye['eye_pressure'], errors='coerce')
        df_eye = df_eye.dropna().sort_values('time_of_measurement')
        df_eye['ewma'] = df_eye['eye_pressure'].ewm(alpha=alpha, adjust=False).mean()
        
        pdf = df_eye.copy()
        pdf.set_index('time_of_measurement', inplace=True)
        resampled = pdf['eye_pressure'].resample('1h').mean().interpolate(method='linear')

    # Initialize all figures as empty
    fig_ewma, fig_stl_t, fig_stl_s, fig_stl_r, fig_vf = empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    # --- 2. GENERATE PLOTS CONDITIONALLY ---

    if 'EWMA IOP' in selected_plots:
        fig_ewma = make_subplots(specs=[[{"secondary_y": True}]])
        if not df_eye.empty:
            fig_ewma.add_trace(go.Scatter(x=df_eye['time_of_measurement'], y=df_eye['eye_pressure'], mode='markers', marker=dict(color='rgba(59, 130, 246, 0.3)'), name='Raw IOP'), secondary_y=False)
            fig_ewma.add_trace(go.Scatter(x=df_eye['time_of_measurement'], y=df_eye['ewma'], mode='lines', line=dict(color="#1e750d", width=2.5), name='EWMA'), secondary_y=False)
        
        fig_ewma = add_global_overlays(fig_ewma, df_visits, df_oct, mrw_shift, rnfl_shift, global_overlays)
        
        fig_ewma.update_layout(
            title="IOP EWMA Integrated View", 
            yaxis_title="Intraocular Pressure (mmHg)", 
            yaxis2_title="OCT Thickness (μm)",
            hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20)
        )
        fig_ewma = apply_system_overlays(fig_ewma, limit_iop)

    if 'STL Decomposition' in selected_plots and not resampled.empty:
        if len(resampled) >= stl_period * 2:
            stl = STL(resampled, period=stl_period, robust=False)
            result = stl.fit()
            
            # Sub-plot Trend
            if 'Trend' in stl_components:
                fig_stl_t = make_subplots(specs=[[{"secondary_y": True}]])
                fig_stl_t.add_trace(go.Scatter(x=resampled.index, y=result.trend, mode='lines', line_color='#cf6b3a', name='Trend Component', line_width=3), secondary_y=False)
                fig_stl_t = add_global_overlays(fig_stl_t, df_visits, df_oct, mrw_shift, rnfl_shift, global_overlays)
                fig_stl_t.update_layout(title="STL: Trend", yaxis_title="IOP (mmHg)", yaxis2_title="OCT (μm)", hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
                fig_stl_t = apply_system_overlays(fig_stl_t, limit_iop)

            # Sub-plot Seasonal
            if 'Seasonal' in stl_components:
                fig_stl_s = make_subplots(specs=[[{"secondary_y": True}]])
                fig_stl_s.add_trace(go.Scatter(x=resampled.index, y=result.seasonal, mode='lines', line_color="#22c54b", name='Seasonal Component', line_width=2), secondary_y=False)
                fig_stl_s = add_global_overlays(fig_stl_s, df_visits, df_oct, mrw_shift, rnfl_shift, global_overlays)
                fig_stl_s.update_layout(title="STL: Seasonal", yaxis_title="Variation (mmHg)", yaxis2_title="OCT (μm)", hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
            
            # Sub-plot Residuals
            if 'Residuals' in stl_components:
                fig_stl_r = make_subplots(specs=[[{"secondary_y": True}]])
                fig_stl_r.add_trace(go.Scatter(x=resampled.index, y=result.resid, mode='lines', line_color="#da248e", name='Residual Component', line_width=2), secondary_y=False)
                fig_stl_r = add_global_overlays(fig_stl_r, df_visits, df_oct, mrw_shift, rnfl_shift, global_overlays)
                fig_stl_r.update_layout(title="STL: Residuals", yaxis_title="Variation (mmHg)", yaxis2_title="OCT (μm)", hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))

        else:
            msg = go.Figure().update_layout(title=f"Not enough data points ({len(resampled)}) for an STL period of {stl_period}.", template="plotly_white")
            fig_stl_t, fig_stl_s, fig_stl_r = msg, msg, msg

    # Visual Field (Untouched, just its own data)
    if 'Visual Field' in selected_plots: 
        fig_vf = build_category_fig(df_oct, ['ms_db', 'md_db', 'slv_db'], "Visual Field", "dB")

    return fig_ewma, fig_stl_t, fig_stl_s, fig_stl_r, fig_vf