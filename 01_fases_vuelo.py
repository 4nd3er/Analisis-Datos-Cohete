"""
SCRIPT 1: ANÁLISIS DE FASES DE VUELO
=====================================
Detecta automáticamente:
- Fase de ascenso (altitud aumentando)
- Apogeo (máxima altitud)
- Fase de descenso (altitud disminuyendo)

Genera gráfica interactiva HTML con colores diferentes por fase.
"""

import json
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
from pathlib import Path

def cargar_datos():
    """Carga datos desde JSON"""
    ruta_json = Path(__file__).parent / "DATOSHpaFixed.json"
    
    with open(ruta_json, 'r') as f:
        datos = json.load(f)
    
    # Convertir a DataFrame
    df = pd.DataFrame(datos)
    
    # Convertir tiempo de ms a segundos
    df['tiempo_s'] = df['tiempo_ms'] / 1000
    
    # Normalizar tiempo a 4 segundos de vuelo real
    # Mapear el tiempo de los datos (0-1209.69s) a 4 segundos reales
    tiempo_max_datos = df['tiempo_s'].max()
    df['tiempo_real'] = (df['tiempo_s'] / tiempo_max_datos) * 4  # Escalar a 4 segundos
    
    # Altitud real del cohete: 13.98 m
    # Mapear la presión-altitud a la altura real máxima de 13.98m
    altitud_maxima_real = 13.98
    
    # Usar presión para estimar altitud relativa, luego escalarla
    P0 = 101325  # Pa
    T0 = 288.15  # K
    g = 9.81
    R = 287.05
    
    presion_pa = df['presion'] * 100  # Convertir hPa a Pa
    temp_k = df['temperatura'] + 273.15
    
    h_relativa = (T0 / 0.0065) * ((presion_pa / P0) ** (-0.0065 * R / g) - 1)
    
    # Normalizar a altura máxima real
    h_min = h_relativa.min()
    h_max = h_relativa.max()
    h_rango = h_max - h_min
    
    # Mapear al rango real (0 a 13.98m)
    if h_rango != 0:
        df['altitud'] = ((h_relativa - h_min) / h_rango) * altitud_maxima_real
    else:
        df['altitud'] = altitud_maxima_real / 2
    
    return df

def detectar_fases(df, ventana=51):
    """
    Detecta las tres fases del vuelo
    - Ascenso: altitud aumentando
    - Apogeo: máxima altitud
    - Descenso: altitud disminuyendo
    """
    
    altitud = df['altitud'].values
    
    # Suavizar altitud para detectar cambios
    if len(altitud) > ventana:
        altitud_suavizada = savgol_filter(altitud, ventana, 3)
    else:
        altitud_suavizada = altitud
    
    # Calcular derivada (cambio de altitud)
    derivada = np.gradient(altitud_suavizada)
    
    # Encontrar apogeo (máxima altitud)
    idx_apogeo = np.argmax(altitud)
    
    # Detectar fases
    fases = []
    fase_actual = None
    idx_cambio_fase = []
    
    for i in range(len(derivada) - 1):
        if derivada[i] > 0:  # Ascenso
            nueva_fase = 'Ascenso'
        elif derivada[i] < 0:  # Descenso
            nueva_fase = 'Descenso'
        else:
            nueva_fase = fase_actual
        
        if nueva_fase != fase_actual:
            fase_actual = nueva_fase
            idx_cambio_fase.append(i)
            fases.append(nueva_fase)
    
    return altitud_suavizada, derivada, idx_apogeo, idx_cambio_fase, fases

def crear_grafica_interactiva(df, altitud_suavizada, derivada, idx_apogeo, idx_cambio_fase):
    """
    Crea gráfica interactiva con Plotly
    """
    
    tiempo = df['tiempo_real'].values  # Usar tiempo real en segundos
    altitud_original = df['altitud'].values
    
    # Detectar puntos de cambio de fase
    ascenso_mask = np.zeros(len(tiempo), dtype=bool)
    descenso_mask = np.zeros(len(tiempo), dtype=bool)
    
    if idx_cambio_fase:
        # Fase 1: Ascenso (inicio hasta primer cambio o apogeo)
        fin_ascenso = min(idx_apogeo, idx_cambio_fase[0] if idx_cambio_fase else len(tiempo))
        ascenso_mask[:fin_ascenso] = True
        
        # Fase 2: Descenso (después del apogeo)
        descenso_mask[idx_apogeo:] = True
    else:
        # Si no hay cambios detectados, usar apogeo como referencia
        ascenso_mask[:idx_apogeo] = True
        descenso_mask[idx_apogeo:] = True
    
    # Crear figura con Plotly
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Altitud vs Tiempo (Fases de Vuelo - 4 segundos reales)", "Velocidad Vertical (Derivada)"),
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
        vertical_spacing=0.12
    )
    
    # Panel 1: Altitud con fases coloreadas
    # Ascenso
    fig.add_trace(
        go.Scatter(
            x=tiempo[ascenso_mask],
            y=altitud_original[ascenso_mask],
            mode='lines',
            name='Ascenso',
            line=dict(color='#00AA44', width=3),
            hovertemplate='<b>Ascenso</b><br>Tiempo: %{x:.2f}s<br>Altitud: %{y:.2f}m<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Descenso
    fig.add_trace(
        go.Scatter(
            x=tiempo[descenso_mask],
            y=altitud_original[descenso_mask],
            mode='lines',
            name='Descenso',
            line=dict(color='#FF6B6B', width=3),
            hovertemplate='<b>Descenso</b><br>Tiempo: %{x:.2f}s<br>Altitud: %{y:.2f}m<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Marcar apogeo
    fig.add_trace(
        go.Scatter(
            x=[tiempo[idx_apogeo]],
            y=[altitud_original[idx_apogeo]],
            mode='markers+text',
            name='Apogeo',
            marker=dict(size=15, color='#FFD700', symbol='star', line=dict(color='#FF8C00', width=2)),
            text=[f"Apogeo<br>{altitud_original[idx_apogeo]:.2f}m<br>t={tiempo[idx_apogeo]:.2f}s"],
            textposition="top center",
            hovertemplate='<b>APOGEO</b><br>Tiempo: %{x:.2f}s<br>Altitud máxima: %{y:.2f}m<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Panel 2: Derivada (velocidad vertical)
    fig.add_trace(
        go.Scatter(
            x=tiempo,
            y=derivada,
            mode='lines',
            name='Velocidad Vertical',
            line=dict(color='#0066FF', width=2),
            hovertemplate='Tiempo: %{x:.2f}s<br>dh/dt: %{y:.3f}m/s<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Línea de referencia en y=0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
    
    # Actualizar ejes
    fig.update_xaxes(title_text="Tiempo (segundos)", row=1, col=1)
    fig.update_yaxes(title_text="Altitud (metros)", row=1, col=1)
    
    fig.update_xaxes(title_text="Tiempo (segundos)", row=2, col=1)
    fig.update_yaxes(title_text="Velocidad Vertical (m/s)", row=2, col=1)
    
    # Estilo general
    fig.update_layout(
        title={
            'text': "<b>ANÁLISIS DE FASES DE VUELO DEL COHETE</b><br><sub>Altura máxima real: 13.98 m | Tiempo total: 4 segundos</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1f77b4'}
        },
        hovermode='x unified',
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        height=800,
        showlegend=True,
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1)
    )
    
    return fig

def main():
    print("\n" + "="*70)
    print("  SCRIPT 1: ANÁLISIS DE FASES DE VUELO DEL COHETE")
    print("="*70)
    
    print("\n✓ Cargando datos...")
    df = cargar_datos()
    print(f"  → {len(df)} puntos de datos cargados")
    print(f"  → Rango de tiempo real: {df['tiempo_real'].min():.2f}s - {df['tiempo_real'].max():.2f}s")
    print(f"  → Rango de altitud: {df['altitud'].min():.2f}m - {df['altitud'].max():.2f}m")
    print(f"  → Altura máxima real: 13.98 m")
    
    print("\n✓ Detectando fases de vuelo...")
    altitud_suavizada, derivada, idx_apogeo, idx_cambio_fase, fases = detectar_fases(df)
    
    print(f"  → Apogeo detectado en: t={df['tiempo_real'].iloc[idx_apogeo]:.2f}s")
    print(f"  → Altitud máxima: {df['altitud'].iloc[idx_apogeo]:.2f}m")
    print(f"  → Número de cambios de fase detectados: {len(idx_cambio_fase)}")
    
    print("\n✓ Generando gráfica interactiva...")
    fig = crear_grafica_interactiva(df, altitud_suavizada, derivada, idx_apogeo, idx_cambio_fase)
    
    # Guardar HTML
    archivo_html = Path(__file__).parent / "01_fases_vuelo.html"
    fig.write_html(str(archivo_html))
    print(f"  → Gráfica guardada en: {archivo_html}")
    
    # Abrir en navegador
    print("\n✓ Abriendo en navegador...")
    webbrowser.open(f'file://{archivo_html.absolute()}')
    
    print("\n" + "="*70)
    print("  ✓ ANÁLISIS COMPLETADO")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
