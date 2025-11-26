import json
import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import webbrowser


def pressure_to_altitude_hpa(p_hpa, p0=1013.25):
    """Convert pressure in hPa to altitude in meters (approx.)
    using the barometric formula: h = 44330 * (1 - (P/P0)^(1/5.255))
    """
    p = np.array(p_hpa, dtype=float)
    return 44330.0 * (1.0 - (p / float(p0)) ** (1.0 / 5.255))


def load_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # normalize into DataFrame
    df = pd.DataFrame(data)

    # Identify time column: prefer 'tiempo' then 'tiempo_ms'
    if 'tiempo' in df.columns:
        t = df['tiempo'].astype(float)
    elif 'tiempo_ms' in df.columns:
        t = df['tiempo_ms'].astype(float) / 1000.0
    else:
        # fallback: use index as seconds
        t = pd.Series(np.arange(len(df)), dtype=float)

    # Identify altitude column: if exists, use it. Otherwise compute from pressure
    if 'altitud' in df.columns:
        alt = df['altitud'].astype(float)
    elif 'presion' in df.columns:
        alt = pressure_to_altitude_hpa(df['presion'].astype(float))
    else:
        raise ValueError('No se encontró columna `altitud` ni `presion` en el archivo')

    return t.values, np.array(alt)


def detect_phases(t, alt, smooth_window=5):
    # Smooth altitude to reduce noise for presentation
    s = pd.Series(alt)
    if smooth_window > 1:
        alt_s = s.rolling(window=smooth_window, center=True, min_periods=1).mean().values
    else:
        alt_s = alt

    apogee_idx = int(np.nanargmax(alt_s))

    phases = np.array([''] * len(alt), dtype=object)
    phases[:apogee_idx] = 'ascenso'
    phases[apogee_idx] = 'apogeo'
    if apogee_idx + 1 < len(alt):
        phases[apogee_idx + 1:] = 'descenso'

    return phases, apogee_idx, alt_s


def detect_peaks(alt_s, window_baseline=101, threshold_k=3):
    """Detectar picos locales significativos en la señal suavizada.

    - window_baseline: ventana (muestras) para calcular la mediana de fondo.
    - threshold_k: múltiplo de la desviación estándar del ruido requerido para considerar un pico.
    Devuelve índices de picos.
    """
    s = pd.Series(alt_s)
    # baseline: mediana local
    baseline = s.rolling(window=window_baseline, center=True, min_periods=1).median().values
    noise = alt_s - baseline
    sigma = np.nanstd(noise)

    # condición de máximo local simple
    shifted_left = np.roll(alt_s, 1)
    shifted_right = np.roll(alt_s, -1)
    is_local_max = (alt_s > shifted_left) & (alt_s > shifted_right)

    # evitar extremos de roll
    is_local_max[0] = False
    is_local_max[-1] = False

    # amplitud sobre baseline
    amp = alt_s - baseline
    thresh = threshold_k * max(sigma, 1e-6)

    peaks_idx = np.where(is_local_max & (amp > thresh))[0]
    return peaks_idx, baseline, amp, thresh


def segment_launches(peaks_idx, t, alt_rel, alt_s_rel, pre_seconds=10, post_seconds=30):
    """Extraer ventanas alrededor de cada pico para comparar lanzamientos.

    - pre_seconds / post_seconds: segundos antes y después del pico para incluir en la ventana.
    Devuelve lista de dicts: {'index', 't', 'alt', 't0'} donde t0 es tiempo relativo al pico.
    """
    segments = []
    if len(t) < 2:
        return segments
    dt = np.median(np.diff(t))
    pre_samples = int(round(pre_seconds / dt))
    post_samples = int(round(post_seconds / dt))

    for idx in peaks_idx:
        start = max(0, idx - pre_samples)
        end = min(len(t) - 1, idx + post_samples)
        seg_t = t[start:end+1] - t[idx]
        seg_alt = alt_rel[start:end+1]
        # No filtrar, incluir todos los datos (incluso valores cercanos a cero o negativos)
        if len(seg_alt) < 3:
            continue
        segments.append({'index': int(idx), 't': seg_t, 'alt': seg_alt, 'peak_time': float(t[idx])})

    return segments


def plot_launch_comparison(segments, out_html=None, open_browser=True, ylim=(1, 15)):
    """Graficar todas las ventanas (lanzamientos) en subplots apilados (uno encima de otro).

    Cada lanzamiento ocupa una fila; muestra ascenso y descenso alrededor del pico.
    """
    n = len(segments)
    if n == 0:
        print('No hay segmentos para comparar.')
        return

    fig = make_subplots(rows=n, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                        subplot_titles=[''] * n)  # Sin títulos en los subplots

    # palette: usar colores consistentes por lanzamiento
    palette = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']

    for i, seg in enumerate(segments, start=1):
        # mostrar TODA la ventana: ascenso (t <= 0) y descenso (t > 0)
        x = seg['t']
        y = seg['alt']
        
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=f'Lanzamiento {i}', 
                                 line=dict(color=palette[(i-1) % len(palette)], width=3),
                                 showlegend=(i==1), legendgroup='launches'), row=i, col=1)
        
        # marcar pico en la ventana (t=0) si está presente en la ventana
        idx0 = int(np.argmin(np.abs(seg['t'] - 0)))
        peak_x = seg['t'][idx0]
        peak_y = seg['alt'][idx0]
        
        fig.add_trace(go.Scatter(x=[peak_x], y=[peak_y], mode='markers', 
                                 marker=dict(size=12, color='black'), showlegend=False), row=i, col=1)
        fig.update_yaxes(title_text='Alt (m)', range=[ylim[0], ylim[1]], row=i, col=1)
        
        # Agregar anotación centrada entre gráficas con el texto del lanzamiento
        fig.add_annotation(
            text=f'Lanzamiento {i} (t={segments[i-1]["peak_time"]:.1f}s)',
            xref='paper', yref='paper',
            x=0.5, y=1.0 - (i-1)/(n) - 0.08 if i < n else None,
            showarrow=False,
            font=dict(size=12, color='gray'),
            xanchor='center'
        ) if i < n else None

    # Ocultar etiquetas X en todos menos el último subplot
    for ridx in range(1, n):
        fig.update_xaxes(row=ridx, col=1, showticklabels=False)
    # Asegurar que el último subplot muestre etiquetas X
    fig.update_xaxes(row=n, col=1, showticklabels=True, title_text='Tiempo relativo al pico (s)')

    fig.update_layout(title='Lanzamiento 1 (t=335.0s)',
                      template='plotly_white', height=200*n+100, 
                      font=dict(size=11), 
                      legend=dict(x=1.05, y=1, xanchor='left', yanchor='top'),
                      margin=dict(t=60, b=80, l=60, r=150))

    if out_html:
        pio.write_html(fig, file=out_html, auto_open=False, include_plotlyjs='cdn')
        print(f'HTML comparativo guardado en: {out_html}')
        if open_browser:
            webbrowser.open_new_tab('file://' + os.path.abspath(out_html))
    else:
        tmp = os.path.join(os.path.dirname(__file__), 'launches_comparison.html')
        pio.write_html(fig, file=tmp, auto_open=False, include_plotlyjs='cdn')
        webbrowser.open_new_tab('file://' + os.path.abspath(tmp))


def plot_phases(t, alt, phases, apogee_idx, alt_s, out_path=None):
    plt.style.use('seaborn-whitegrid')
    fig, ax = plt.subplots(figsize=(11, 6))

    # Plot ascending
    mask_asc = phases == 'ascenso'
    mask_desc = phases == 'descenso'
    mask_ap = phases == 'apogeo'

    ax.plot(t[mask_asc], alt[mask_asc], color='#2ca02c', lw=2, label='Ascenso')
    ax.plot(t[mask_desc], alt[mask_desc], color='#d62728', lw=2, label='Descenso')
    # plot full smoothed line for clarity (light color)
    ax.plot(t, alt_s, color='gray', lw=1, alpha=0.6, label='Altitud (suavizada)')

    # Mark apogee
    ax.scatter([t[apogee_idx]], [alt[apogee_idx]], color='black', s=60, zorder=5, label='Apogeo')
    ax.annotate(f"Apogeo\n{alt[apogee_idx]:.1f} m\n{t[apogee_idx]:.1f} s",
                xy=(t[apogee_idx], alt[apogee_idx]), xytext=(10, 30), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='black', alpha=0.9))

    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Altitud (m)')
    ax.set_title('Altitud vs Tiempo — Fases: Ascenso / Apogeo / Descenso')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()

    if out_path:
        fig.savefig(out_path, dpi=200)
        print(f'Gráfica guardada en: {out_path}')

    plt.show()


def plot_phases_interactive(t, alt, phases, apogee_idx, alt_s, out_html=None, open_browser=True):
    """Crear una figura interactiva con Plotly y opcionalmente abrir en el navegador."""
    # Colores
    asc_color = '#2ca02c'
    desc_color = '#d62728'
    smooth_color = 'gray'

    fig = go.Figure()

    # Ascenso
    asc_mask = phases == 'ascenso'
    if asc_mask.any():
        fig.add_trace(go.Scatter(x=t[asc_mask], y=alt[asc_mask], mode='lines',
                                 name='Ascenso', line=dict(color=asc_color, width=3)))

    # Descenso
    desc_mask = phases == 'descenso'
    if desc_mask.any():
        fig.add_trace(go.Scatter(x=t[desc_mask], y=alt[desc_mask], mode='lines',
                                 name='Descenso', line=dict(color=desc_color, width=3)))

    # Suavizada
    fig.add_trace(go.Scatter(x=t, y=alt_s, mode='lines', name='Altitud (suavizada)',
                             line=dict(color=smooth_color, width=1), opacity=0.6))

    # Apogeo
    fig.add_trace(go.Scatter(x=[t[apogee_idx]], y=[alt[apogee_idx]], mode='markers+text',
                             name='Apogeo', marker=dict(color='black', size=10),
                             text=[f"Apogeo\n{alt[apogee_idx]:.1f} m\n{t[apogee_idx]:.1f} s"],
                             textposition='top right'))

    fig.update_layout(title='Altitud vs Tiempo — Fases: Ascenso / Apogeo / Descenso',
                      xaxis_title='Tiempo (s)', yaxis_title='Altitud (m)',
                      template='plotly_white', legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

    if out_html:
        # Default to write html
        pio.write_html(fig, file=out_html, auto_open=False, include_plotlyjs='cdn')
        print(f'HTML interactivo guardado en: {out_html}')
        if open_browser:
            webbrowser.open_new_tab('file://' + os.path.abspath(out_html))
    else:
        # abrir temporalmente en navegador si no se especifica path
        tmp = os.path.join(os.path.dirname(__file__), 'temp_altitud_fases.html')
        pio.write_html(fig, file=tmp, auto_open=False, include_plotlyjs='cdn')
        webbrowser.open_new_tab('file://' + os.path.abspath(tmp))


def plot_peaks_only(t, alt, alt_s, peaks_idx, out_html=None, open_browser=True, window=20):
    """Generar una página HTML con subplots alrededor de cada pico para enfocarse en los ascensos (picos).
    window: número de segundos a cada lado (aprox según muestreo) para mostrar.
    """
    # Estimar paso de tiempo medio
    dt = np.median(np.diff(t)) if len(t) > 1 else 1.0
    half_samples = int(max(1, round(window / dt)))

    rows = len(peaks_idx)
    fig = go.Figure()

    for i, idx in enumerate(peaks_idx):
        start = max(0, idx - half_samples)
        end = min(len(t) - 1, idx + half_samples)
        x = t[start:end+1]
        y = alt[start:end+1]
        y_s = alt_s[start:end+1]
        name = f'Pico {i+1} (t={t[idx]:.1f}s)'
        # mostrar solo la parte de ascenso alrededor del pico (tiempos relativos <= 0)
        x_rel = x - t[idx]
        mask_ascent = x_rel <= 0
        if mask_ascent.sum() < 2:
            x_plot = x
            y_plot = y
        else:
            x_plot = x_rel[mask_ascent]
            y_plot = y[mask_ascent]
        fig.add_trace(go.Scatter(x=x_plot, y=y_plot, mode='lines', name=name, visible=True))
        fig.add_trace(go.Scatter(x=[0], y=[alt[idx]], mode='markers+text', marker=dict(size=10, color='blue'),
                                 text=[f'{alt[idx]:.1f} m'], textposition='top center', showlegend=False))

    fig.update_layout(title=f'Ventanas alrededor de {len(peaks_idx)} picos detectados', xaxis_title='Tiempo (s)', yaxis_title='Altitud (m)', template='plotly_white')

    if out_html:
        pio.write_html(fig, file=out_html, auto_open=False, include_plotlyjs='cdn')
        print(f'HTML de picos guardado en: {out_html}')
        if open_browser:
            webbrowser.open_new_tab('file://' + os.path.abspath(out_html))
    else:
        tmp = os.path.join(os.path.dirname(__file__), 'altitud_peaks.html')
        pio.write_html(fig, file=tmp, auto_open=False, include_plotlyjs='cdn')
        webbrowser.open_new_tab('file://' + os.path.abspath(tmp))


def main():
    parser = argparse.ArgumentParser(description='Detectar fases y apogeo a partir de DATOSHpaFixed.json')
    parser.add_argument('--input', '-i', default='DATOSHpaFixed.json', help='Ruta al archivo JSON (por defecto: DATOSHpaFixed.json)')
    parser.add_argument('--out', '-o', default='altitud_fases.png', help='Ruta PNG de salida para la figura')
    parser.add_argument('--smooth', '-s', type=int, default=9, help='Ventana de suavizado (enteros, odd preferible)')
    parser.add_argument('--html', '-b', action='store_true', help='Generar HTML interactivo y abrir en el navegador (usa Plotly)')
    parser.add_argument('--html-out', type=str, default='altitud_fases.html', help='Ruta del HTML interactivo de salida')
    parser.add_argument('--detect-peaks', action='store_true', help='Detectar picos significativos en la fase de ascenso')
    parser.add_argument('--peak-window-baseline', type=int, default=101, help='Ventana para mediana de baseline (muestras)')
    parser.add_argument('--peak-threshold-k', type=float, default=3.0, help='Umbral en múltiplos de sigma para considerar un pico')
    parser.add_argument('--force-top-n', action='store_true', help='Forzar selección de top-N picos dùrante la selección aunque estén por debajo del umbral')
    parser.add_argument('--pre-seconds', type=float, default=10.0, help='Segundos antes del pico para segmentar la ventana del lanzamiento')
    parser.add_argument('--post-seconds', type=float, default=30.0, help='Segundos después del pico para segmentar la ventana del lanzamiento')
    parser.add_argument('--baseline-height', type=float, default=None, help='Valor real (m) para calibrar la amplitud del pico principal, p.ej. 13.98')
    parser.add_argument('--zero-at-min', action='store_true', help='Restar el valor mínimo de altitud para que el mínimo sea 0')
    parser.add_argument('--only-launches', action='store_true', help='Al generar HTML con picos, abrir solo la página de comparación de lanzamientos (no la principal)')
    parser.add_argument('--peaks-out', type=str, default='peaks.csv', help='CSV de salida con picos detectados')
    parser.add_argument('--peaks-only', action='store_true', help='Generar página con ventanas enfocadas en cada pico')
    parser.add_argument('--top-n', type=int, default=3, help='Número de lanzamientos (picos) principales a comparar')
    args = parser.parse_args()

    # Determine path relative to script if not absolute
    path = args.input
    if not os.path.isabs(path):
        # assume file is in the same folder as this script
        base = os.path.dirname(__file__)
        path = os.path.join(base, path)

    t, alt_raw = load_data(path)

    # Aplicar ajuste de cero en el mínimo si se solicita
    if args.zero_at_min:
        min_val = np.nanmin(alt_raw)
        alt = alt_raw - min_val
    else:
        alt = alt_raw.copy()

    # Calcular altitud relativa inicial (antes de cualquier calibrado por baseline)
    if args.zero_at_min:
        alt_rel = alt.copy()
    else:
        alt_rel = alt - alt[0]

    # Suavizar y detectar apogeo en la señal ajustada
    phases, apogee_idx, alt_s = detect_phases(t, alt_rel, smooth_window=args.smooth)
    print(f'Apogeo en índice {apogee_idx}: tiempo={t[apogee_idx]:.2f} s, altitud={alt_rel[apogee_idx]:.2f} m')
    # Enmascarar valores no finitos o <= 0 (datos muertos o ceros)
    valid_global = np.isfinite(alt_rel) & (alt_rel > 0)
    if valid_global.sum() == 0:
        print('No se encontraron datos válidos después de filtrar ceros/muertos.')
        return

    # preparar señal suavizada relativa
    s_rel = pd.Series(alt_rel)
    alt_s_rel = s_rel.rolling(window=args.smooth, center=True, min_periods=1).mean().values

    # Detección de picos opcional
    peaks_idx = np.array([], dtype=int)
    if args.detect_peaks:
        peaks_idx, baseline, amp, thresh = detect_peaks(alt_s_rel, window_baseline=args.peak_window_baseline, threshold_k=args.peak_threshold_k)
        print(f'Detectados {len(peaks_idx)} picos (umbral={thresh:.3f} m)')
        # si pedimos forzar top-N y no encontramos suficientes picos por el umbral,
        # seleccionar los máximos locales por amplitud sin aplicar el umbral
        if args.force_top_n and (len(peaks_idx) < args.top_n):
            # calcular máximos locales (sin umbral)
            shifted_left = np.roll(alt_s_rel, 1)
            shifted_right = np.roll(alt_s_rel, -1)
            is_local_max_all = (alt_s_rel > shifted_left) & (alt_s_rel > shifted_right)
            is_local_max_all[0] = False
            is_local_max_all[-1] = False
            all_max_idx = np.where(is_local_max_all)[0]
            if len(all_max_idx) > 0:
                # usar amplitud sobre baseline si está disponible, sino usar alt_s_rel
                try:
                    amps_all = amp[all_max_idx]
                except Exception:
                    amps_all = alt_s_rel[all_max_idx]
                order_all = np.argsort(amps_all)[::-1]
                sel_all = order_all[:args.top_n]
                chosen = all_max_idx[sel_all]
                # ordenar por tiempo
                peaks_idx = np.array(sorted(chosen, key=lambda ii: float(t[ii])))
                print(f'Forzado top-{args.top_n} (sin umbral): {peaks_idx.tolist()}')
        else:
            # seleccionar los top-N picos por amplitud sobre baseline (si hay suficientes)
            if len(peaks_idx) > 0 and args.top_n > 0:
                amps = amp[peaks_idx]
                order = np.argsort(amps)[::-1]
                sel = order[:args.top_n]
                peaks_idx = peaks_idx[sel]
                # ordenar por tiempo ascendente para presentación
                peaks_idx = np.array(sorted(peaks_idx, key=lambda ii: float(t[ii])))
                print(f'Seleccionados top-{args.top_n} picos: {peaks_idx.tolist()}')
        # export CSV si solicitado
        if args.peaks_out:
            outcsv = args.peaks_out
            if not os.path.isabs(outcsv):
                outcsv = os.path.join(os.path.dirname(path), outcsv)
            with open(outcsv, 'w', newline='', encoding='utf-8') as cf:
                import csv
                writer = csv.writer(cf)
                writer.writerow(['index', 'tiempo_s', 'altitud_m', 'amplitud_sobre_baseline_m'])
                for idx in peaks_idx:
                    writer.writerow([int(idx), float(t[idx]), float(alt_rel[idx]), float(amp[idx])])
            print(f'Picos exportados a: {outcsv}')

    # Si se indicó una altura de referencia real, calibrar la señal para que el pico principal
    # coincida con ese valor (después de haber seleccionado picos si era necesario)
    if args.baseline_height is not None:
        # decidir referencia actual: usar el máximo entre picos detectados si disponibles
        if args.detect_peaks and len(peaks_idx) > 0:
            current_ref = float(np.nanmax(alt_rel[peaks_idx]))
        else:
            current_ref = float(np.nanmax(alt_rel))

        if current_ref <= 0 or np.isnan(current_ref):
            print('No se pudo calibrar con baseline: referencia actual inválida (<=0 o NaN). Se omite calibrado.')
        else:
            scale = float(args.baseline_height) / current_ref
            alt_rel = alt_rel * scale
            alt_s_rel = alt_s_rel * scale
            print(f'Calibrado: escala aplicada {scale:.4f} para llevar referencia {current_ref:.3f} -> {args.baseline_height:.3f} m')

    if args.html:
        html_path = args.html_out
        if not os.path.isabs(html_path):
            html_path = os.path.join(os.path.dirname(path), html_path)
        # Si se detectaron picos, márcalos también en la gráfica
        if args.detect_peaks and len(peaks_idx) > 0:
            # generar figura interactiva y abrirla
            plot_phases_interactive(t, alt_rel, phases, apogee_idx, alt_s_rel, out_html=html_path, open_browser=False)
            # segmentar lanzamientos y mostrar comparación (filtrando ceros)
            segments = segment_launches(peaks_idx, t, alt_rel, alt_s_rel, pre_seconds=args.pre_seconds, post_seconds=args.post_seconds)
            if len(segments) > 0:
                comp_html = os.path.splitext(html_path)[0] + '_launches.html'
                # limitar a 1-15 m como pediste
                # No abrir aquí: dejar que `main()` controle qué página abrir para evitar abrir dos pestañas.
                plot_launch_comparison(segments, out_html=comp_html, open_browser=False, ylim=(1, 15))
            if args.peaks_only:
                peaks_html = os.path.splitext(html_path)[0] + '_peaks.html'
                plot_peaks_only(t, alt_rel, alt_s_rel, peaks_idx, out_html=peaks_html, open_browser=True, window=20)
            else:
                # si no hay picos o no se generó comparativa, abrir la página principal
                if not args.only_launches:
                    webbrowser.open_new_tab('file://' + os.path.abspath(html_path))
                else:
                    # si se pidió 'only launches' y se generó comparativa, abrir solo la comparativa
                    if len(segments) > 0:
                        webbrowser.open_new_tab('file://' + os.path.abspath(comp_html))
                    else:
                        # fallback: abrir la principal si no hay comparativa
                        webbrowser.open_new_tab('file://' + os.path.abspath(html_path))
        else:
            # Si se pidió abrir solo la comparativa, no abrir la principal aquí (la comparativa se abrirá si se genera)
            open_main = not args.only_launches
            plot_phases_interactive(t, alt_rel, phases, apogee_idx, alt_s_rel, out_html=html_path, open_browser=open_main)
    else:
        out_path = args.out
        if not os.path.isabs(out_path):
            out_path = os.path.join(os.path.dirname(path), out_path)

        # cuando se guarda con matplotlib, usar altitud relativa y limitar eje Y
        plt_alt = alt_rel
        plt_smooth = alt_s_rel
        # crear figura rápida con límites
        plt.style.use('seaborn-whitegrid')
        fig, ax = plt.subplots(figsize=(11, 6))
        mask_asc = phases == 'ascenso'
        mask_desc = phases == 'descenso'
        ax.plot(t[mask_asc], plt_alt[mask_asc], color='#2ca02c', lw=2, label='Ascenso')
        ax.plot(t[mask_desc], plt_alt[mask_desc], color='#d62728', lw=2, label='Descenso')
        ax.plot(t, plt_smooth, color='gray', lw=1, alpha=0.6, label='Altitud (suavizada)')
        ax.scatter([t[apogee_idx]], [plt_alt[apogee_idx]], color='black', s=60, zorder=5, label='Apogeo')
        ax.set_xlabel('Tiempo (s)')
        ax.set_ylabel('Altitud relativa (m)')
        ax.set_ylim(1, 15)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_path, dpi=200)
        print(f'Gráfica guardada en: {out_path}')
        plt.show()


if __name__ == '__main__':
    main()
