import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import STL # NEW IMPORT
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

# ADDED new parameters and selected_plots to the function signature
def generate_all_figures(selected_patient, alpha, shift_days, bb_window, bb_k, stl_period, selected_plots, limit_iop):
    empty_fig = go.Figure().update_layout(template="plotly_white", title="Select a patient to view data")
    
    if not selected_patient or not selected_plots:
        return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    # Provide safe defaults if sliders are still loading
    alpha = alpha if alpha is not None else 0.3
    shift_days = shift_days if shift_days is not None else 0
    bb_window = bb_window if bb_window is not None else 12
    bb_k = bb_k if bb_k is not None else 2.0
    stl_period = stl_period if stl_period is not None else 24

    df_eye, df_oct = get_patient_data(selected_patient)

    # --- 1. DATA PREP & RESAMPLING ---
    resampled = pd.Series(dtype=float)
    if not df_eye.empty:
        df_eye['time_of_measurement'] = pd.to_datetime(df_eye['time_of_measurement'], errors='coerce')
        df_eye['eye_pressure'] = pd.to_numeric(df_eye['eye_pressure'], errors='coerce')
        df_eye = df_eye.dropna().sort_values('time_of_measurement')
        df_eye['ewma'] = df_eye['eye_pressure'].ewm(alpha=alpha, adjust=False).mean()
        
        # Resample for Advanced Math (Bollinger & STL)
        pdf = df_eye.copy()
        pdf.set_index('time_of_measurement', inplace=True)
        # Assuming 'eye_pressure' is the column name based on previous queries
        resampled = pdf['eye_pressure'].resample('1h').mean().interpolate(method='linear')

    # Initialize all figures as empty
    fig_shift, fig_ewma, fig_boll, fig_stl, fig_vf, fig_mrw, fig_rnflt, fig_gat_argos = empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    # --- 2. GENERATE PLOTS CONDITIONALLY ---
    if 'Shift Analysis' in selected_plots:
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

    if 'EWMA IOP' in selected_plots:
        fig_ewma = go.Figure()
        if not df_eye.empty:
            fig_ewma.add_trace(go.Scatter(x=df_eye['time_of_measurement'], y=df_eye['eye_pressure'], mode='markers', marker=dict(color='rgba(59, 130, 246, 0.3)'), name='Raw'))
            fig_ewma.add_trace(go.Scatter(x=df_eye['time_of_measurement'], y=df_eye['ewma'], mode='lines', line=dict(color="#1e750d", width=2.5), name='EWMA'))
        fig_ewma.update_layout(title="IOP & EWMA", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))

    if 'Bollinger Bands' in selected_plots and not resampled.empty:
        rolling_mean = resampled.rolling(window=bb_window, center=True).mean()
        rolling_std = resampled.rolling(window=bb_window, center=True).std()
        upper_band = rolling_mean + (bb_k * rolling_std)
        lower_band = rolling_mean - (bb_k * rolling_std)
        anomalies_high = resampled[resampled > upper_band]
        anomalies_low = resampled[resampled < lower_band]

        fig_boll = go.Figure()
        fig_boll.add_trace(go.Scatter(x=resampled.index, y=upper_band, mode='lines', line_color='rgba(200,200,200,0.2)', name='Upper Band'))
        fig_boll.add_trace(go.Scatter(x=resampled.index, y=lower_band, mode='lines', line_color='rgba(200,200,200,0.2)', fill='tonexty', name='Lower Band'))
        fig_boll.add_trace(go.Scatter(x=resampled.index, y=rolling_mean, mode='lines', line=dict(color='#cf6b3a', width=2), name='Rolling Mean'))
        fig_boll.add_trace(go.Scatter(x=resampled.index, y=resampled, mode='lines', line=dict(color='#3b82f6', width=1.5), name='IOP Signal'))
        fig_boll.add_trace(go.Scatter(x=anomalies_high.index, y=anomalies_high, mode='markers', marker=dict(color='red', size=8, symbol='x'), name='High Anomaly'))
        fig_boll.add_trace(go.Scatter(x=anomalies_low.index, y=anomalies_low, mode='markers', marker=dict(color='orange', size=8, symbol='x'), name='Low Anomaly'))
        fig_boll.update_layout(title=f"Statistical Process Control | Window: {bb_window}h, k={bb_k}", hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))

    if 'STL Decomposition' in selected_plots and not resampled.empty:
        if len(resampled) >= stl_period * 2:
            stl = STL(resampled, period=stl_period, robust=False)
            result = stl.fit()
            fig_stl = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=("Observed", "Trend", "Seasonal", "Residuals"))
            fig_stl.add_trace(go.Scatter(x=resampled.index, y=resampled, mode='lines', line_color='#3b82f6', name='Observed'), row=1, col=1)
            fig_stl.add_trace(go.Scatter(x=resampled.index, y=result.trend, mode='lines', line_color='#cf6b3a', name='Trend'), row=2, col=1)
            fig_stl.add_trace(go.Scatter(x=resampled.index, y=result.seasonal, mode='lines', line_color="#22c54b", name='Seasonal'), row=3, col=1)
            fig_stl.add_trace(go.Scatter(x=resampled.index, y=result.resid, mode='lines', line_color="#da248e", name='Residuals'), row=4, col=1)
            fig_stl.update_layout(height=600, template="plotly_white", title_text="Signal Decomposition (STL)", showlegend=False, margin=dict(l=20, r=20, t=50, b=20))
        else:
            fig_stl = go.Figure().update_layout(title=f"Not enough data points ({len(resampled)}) for an STL period of {stl_period}.", template="plotly_white")

    if 'Visual Field' in selected_plots: fig_vf = build_category_fig(df_oct, ['ms_db', 'md_db', 'slv_db'], "Visual Field", "dB")
    if 'MRW' in selected_plots: fig_mrw = build_category_fig(df_oct, ['mrw_ti', 'mrw_t', 'mrw_ts', 'mrw_ns', 'mrw_n', 'mrw_ni', 'mrw_gc', 'mrw_g'], "MRW", "μm")
    if 'RNFLT' in selected_plots: fig_rnflt = build_category_fig(df_oct, ['rnfl_ti', 'rnfl_t', 'rnfl_ts', 'rnfl_ns', 'rnfl_n', 'rnfl_ni', 'rnfl_gc', 'rnfl_g'], "RNFLT", "μm")

    if 'GAT vs ARGOS' in selected_plots:
        df_visits = get_visit_data(selected_patient)
        fig_gat_argos = go.Figure()
        
        if not df_visits.empty:
            df_visits['date'] = pd.to_datetime(df_visits['date'], errors='coerce')
            df_visits = df_visits.sort_values('date')
            
            # We map the continuous X-axis to the dates
            x_vals = df_visits['date']
            
            # We create custom text for the labels: "YYYY-MM-DD<br>VisitLabel"
            custom_labels = df_visits['date'].dt.strftime('%Y-%m-%d') + '<br>(' + df_visits['mnpvislabel'].astype(str) + ')'
            
            # Plot Baseline (GAT)
            fig_gat_argos.add_trace(go.Scatter(
                x=x_vals, y=df_visits['gat_mean'], 
                mode='lines+markers', name='GAT (Clinical Standard)',
                marker=dict(symbol='square', size=8), line=dict(color='#cf6b3a', width=2)
            ))
            
            # Plot Sensor (ARGOS)
            fig_gat_argos.add_trace(go.Scatter(
                x=x_vals, y=df_visits['argos_mean'], 
                mode='lines+markers', name='ARGOS (Sensor)',
                marker=dict(symbol='circle', size=8), line=dict(color='#3b82f6', width=2)
            ))
            
            # Update Layout with our custom X-axis ticks
            fig_gat_argos.update_layout(
                title="Sensor Validation: GAT vs ARGOS Mean IOP",
                yaxis_title="Intraocular Pressure (mmHg)",
                xaxis=dict(
                    tickmode='array',
                    tickvals=x_vals,        # Where the tick goes mathematically
                    ticktext=custom_labels  # What the user actually reads
                ),
                hovermode="x unified",
                template="plotly_white",
                margin=dict(l=20, r=20, t=50, b=60)
            )
        else:
            fig_gat_argos = go.Figure().update_layout(title="No visit data for this patient.", template="plotly_white")



    plots_to_overlay = [fig_shift, fig_ewma, fig_boll, fig_gat_argos]
    for fig in plots_to_overlay:
        if fig.data:  # Only apply if the plot actually generated traces
            fig = apply_system_overlays(fig, limit_iop)

    return fig_shift, fig_ewma, fig_boll, fig_stl, fig_vf, fig_mrw, fig_rnflt, fig_gat_argos