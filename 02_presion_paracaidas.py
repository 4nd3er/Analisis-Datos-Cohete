"""
SCRIPT 2: ANÁLISIS DE PRESIÓN Y DESPLIEGUE DEL PARACAÍDAS
==========================================================
Calcula la derivada de presión para detectar:
- Cambios bruscos durante el descenso
- Punto exacto del despliegue del paracaídas

Genera gráfica interactiva HTML con estilo científico.
"""

import json
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter, find_peaks
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
from pathlib import Path

def cargar_datos():
    """Carga datos desde JSON"""
    ruta_json = Path(__file__).parent / "DATOSHpaFixed.json"
    
    with open(ruta_json, 'r') as f:
        datos = json.load(f)
    
    df = pd.DataFrame(datos)
    df['tiempo_s'] = df['tiempo_ms'] / 1000
    
    # Calcular altitud desde presión
    if 'altitud' not in df.columns:
        P0 = 101325
        T0 = 288.15
        g = 9.81
        R = 287.05
        
        presion_pa = df['presion'] * 100
        temp_k = df['temperatura'] + 273.15
        
        h = (T0 / 0.0065) * ((presion_pa / P0) ** (-0.0065 * R / g) - 1)
        df['altitud'] = h
    
    return df

def calcular_derivada_presion(df, ventana=21):
    """
    Calcula la derivada de presión usando Savitzky-Golay
    La derivada muestra cambios bruscos en la presión
    """
    
    presion = df['presion'].values
    
    # Suavizar presión
    if len(presion) > ventana:
        presion_suavizada = savgol_filter(presion, ventana, 2)
    else:
        presion_suavizada = presion
    
    # Calcular derivada
    derivada = np.gradient(presion_suavizada)
    
    # Convertir a hPa/s
    tiempo = df['tiempo_s'].values
    derivada_temporal = np.gradient(presion_suavizada, tiempo)
    
    return presion_suavizada, derivada_temporal

def detectar_despliegue(df, derivada_temporal, idx_apogeo):
    """
    Detecta el despliegue del paracaídas
    Se manifiesta como un pico en la derivada (cambio abrupto de presión)
    El despliegue ocurre después del apogeo
    """
    
    # Buscar picos en la derivada después del apogeo
    umbral = np.percentile(np.abs(derivada_temporal[idx_apogeo:]), 85)
    
    picos, propiedades = find_peaks(
        np.abs(derivada_temporal[idx_apogeo:]),
        height=umbral,
        distance=20
    )
    
    if len(picos) > 0:
        # El despliegue es el primer pico significativo
        idx_despliegue = idx_apogeo + picos[0]
        magnitud = derivada_temporal[idx_despliegue]
        return idx_despliegue, magnitud
    
    # Si no hay picos claros, buscar cambio en derivada
    cambios = np.abs(np.diff(derivada_temporal[idx_apogeo:]))
    idx_despliegue = idx_apogeo + np.argmax(cambios)
    magnitud = derivada_temporal[idx_despliegue]
    
    return idx_despliegue, magnitud

def crear_grafica_interactiva(df, presion_suavizada, derivada_temporal, idx_apogeo, idx_despliegue):
    """
    Crea gráfica interactiva con Plotly
    """
    
    tiempo = df['tiempo_s'].values
    presion = df['presion'].values
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Presión vs Tiempo", "Derivada de Presión vs Tiempo"),
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
        vertical_spacing=0.12
    )
    
    # Panel 1: Presión
    fig.add_trace(
        go.Scatter(
            x=tiempo,
            y=presion,
            mode='lines',
            name='Presión (datos crudos)',
            line=dict(color='rgba(100, 100, 255, 0.4)', width=1),
            hovertemplate='Tiempo: %{x:.2f}s<br>Presión: %{y:.3f}hPa<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=tiempo,
            y=presion_suavizada,
            mode='lines',
            name='Presión (suavizada)',
            line=dict(color='#0066FF', width=2),
            hovertemplate='Tiempo: %{x:.2f}s<br>Presión suavizada: %{y:.3f}hPa<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Marcar apogeo
    fig.add_trace(
        go.Scatter(
            x=[tiempo[idx_apogeo]],
            y=[presion_suavizada[idx_apogeo]],
            mode='markers+text',
            name='Apogeo',
            marker=dict(size=12, color='#FFD700', symbol='diamond', line=dict(color='#FF8C00', width=2)),
            text=[f"Apogeo<br>t={tiempo[idx_apogeo]:.2f}s"],
            textposition="top center",
            hovertemplate='<b>APOGEO</b><br>Tiempo: %{x:.2f}s<br>Presión: %{y:.3f}hPa<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Panel 2: Derivada de presión
    fig.add_trace(
        go.Scatter(
            x=tiempo,
            y=derivada_temporal,
            mode='lines',
            name='dP/dt',
            line=dict(color='#FF6B6B', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.2)',
            hovertemplate='Tiempo: %{x:.2f}s<br>dP/dt: %{y:.4f}hPa/s<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Línea de referencia
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
    
    # Marcar despliegue del paracaídas
    fig.add_trace(
        go.Scatter(
            x=[tiempo[idx_despliegue]],
            y=[derivada_temporal[idx_despliegue]],
            mode='markers+text',
            name='Despliegue',
            marker=dict(size=14, color='#FF0000', symbol='star', line=dict(color='#8B0000', width=2)),
            text=[f"DESPLIEGUE<br>t={tiempo[idx_despliegue]:.2f}s<br>dP/dt={derivada_temporal[idx_despliegue]:.4f}"],
            textposition="top center",
            hovertemplate='<b>DESPLIEGUE PARACAÍDAS</b><br>Tiempo: %{x:.2f}s<br>dP/dt: %{y:.4f}hPa/s<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Actualizar ejes
    fig.update_xaxes(title_text="Tiempo (segundos)", row=1, col=1)
    fig.update_yaxes(title_text="Presión (hPa)", row=1, col=1)
    
    fig.update_xaxes(title_text="Tiempo (segundos)", row=2, col=1)
    fig.update_yaxes(title_text="Derivada de Presión (hPa/s)", row=2, col=1)
    
    # Estilo general
    fig.update_layout(
        title={
            'text': "<b>ANÁLISIS DE PRESIÓN Y DESPLIEGUE DEL PARACAÍDAS</b>",
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
    print("  SCRIPT 2: ANÁLISIS DE PRESIÓN Y PARACAÍDAS")
    print("="*70)
    
    print("\n✓ Cargando datos...")
    df = cargar_datos()
    print(f"  → {len(df)} puntos de datos cargados")
    
    print("\n✓ Calculando derivada de presión...")
    presion_suavizada, derivada_temporal = calcular_derivada_presion(df)
    print(f"  → Derivada calculada")
    
    print("\n✓ Detectando apogeo...")
    idx_apogeo = np.argmin(df['presion'].values)  # Presión mínima = altitud máxima
    print(f"  → Apogeo en: t={df['tiempo_s'].iloc[idx_apogeo]:.2f}s")
    
    print("\n✓ Detectando despliegue del paracaídas...")
    idx_despliegue, magnitud = detectar_despliegue(df, derivada_temporal, idx_apogeo)
    print(f"  → Despliegue detectado en: t={df['tiempo_s'].iloc[idx_despliegue]:.2f}s")
    print(f"  → Magnitud de cambio: dP/dt = {magnitud:.4f}hPa/s")
    print(f"  → Altitud aproximada: {df['altitud'].iloc[idx_despliegue]:.2f}m")
    
    print("\n✓ Generando gráfica interactiva...")
    fig = crear_grafica_interactiva(df, presion_suavizada, derivada_temporal, idx_apogeo, idx_despliegue)
    
    # Guardar HTML
    archivo_html = Path(__file__).parent / "02_presion_paracaidas.html"
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
