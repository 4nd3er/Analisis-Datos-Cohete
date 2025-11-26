"""
SCRIPT 3: ANÁLISIS DE DENSIDAD AERODINÁMICA
============================================
Calcula la densidad del aire usando:
    ρ = P / (R * T)

Donde:
- P = Presión (Pa)
- R = 287.05 J/(kg·K) (constante específica del aire)
- T = Temperatura (K)

Grafíca: Densidad vs Altitud
"""

import json
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
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
    
    # Calcular altitud desde presión (fórmula barométrica)
    P0 = 101325  # Pa (presión nivel del mar)
    T0 = 288.15  # K
    g = 9.81     # m/s²
    R = 287.05   # J/(kg·K)
    Gamma = 0.0065  # K/m (gradiente adiabático)
    
    presion_pa = df['presion'] * 100  # Convertir hPa a Pa
    temp_k = df['temperatura'] + 273.15  # Convertir °C a K
    
    # Fórmula barométrica
    h = (T0 / Gamma) * ((presion_pa / P0) ** (-Gamma * R / g) - 1)
    df['altitud'] = h
    
    return df, presion_pa, temp_k

def calcular_densidad(presion_pa, temp_k):
    """
    Calcula la densidad del aire usando la ecuación del gas ideal
    
    ρ = P / (R * T)
    
    Donde:
    - ρ: densidad (kg/m³)
    - P: presión absoluta (Pa)
    - R: constante específica del aire = 287.05 J/(kg·K)
    - T: temperatura absoluta (K)
    """
    
    R_aire = 287.05  # J/(kg·K)
    densidad = presion_pa / (R_aire * temp_k)
    
    return densidad

def crear_grafica_interactiva(df, densidad):
    """
    Crea gráfica interactiva con Plotly
    Relación entre densidad y altitud
    """
    
    tiempo = df['tiempo_s'].values
    altitud = df['altitud'].values
    temperatura = df['temperatura'].values
    presion = df['presion'].values
    
    # Ordenar por altitud para mejor visualización
    idx_orden = np.argsort(altitud)
    
    # Crear un color mapping basado en tiempo
    colores_tiempo = np.linspace(0, 1, len(tiempo))
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Densidad vs Altitud",
            "Densidad vs Tiempo",
            "Temperatura vs Altitud",
            "Presión vs Altitud"
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.12
    )
    
    # Panel 1: Densidad vs Altitud (PRINCIPAL)
    fig.add_trace(
        go.Scatter(
            x=altitud,
            y=densidad,
            mode='markers',
            name='Densidad vs Altitud',
            marker=dict(
                size=6,
                color=tiempo,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title="Tiempo (s)",
                    x=0.46,
                    len=0.4
                ),
                line=dict(width=0.5, color='white')
            ),
            hovertemplate='Altitud: %{x:.2f}m<br>Densidad: %{y:.4f}kg/m³<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Agregar línea de tendencia
    z = np.polyfit(altitud, densidad, 3)
    p = np.poly1d(z)
    altitud_suave = np.linspace(altitud.min(), altitud.max(), 100)
    densidad_suave = p(altitud_suave)
    
    fig.add_trace(
        go.Scatter(
            x=altitud_suave,
            y=densidad_suave,
            mode='lines',
            name='Tendencia',
            line=dict(color='red', width=2, dash='dash'),
            hovertemplate='Tendencia<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Panel 2: Densidad vs Tiempo
    fig.add_trace(
        go.Scatter(
            x=tiempo,
            y=densidad,
            mode='lines',
            name='Densidad (t)',
            line=dict(color='#00AA44', width=2),
            hovertemplate='Tiempo: %{x:.2f}s<br>Densidad: %{y:.4f}kg/m³<extra></extra>'
        ),
        row=1, col=2
    )
    
    # Panel 3: Temperatura vs Altitud
    fig.add_trace(
        go.Scatter(
            x=altitud,
            y=temperatura,
            mode='markers',
            name='Temperatura',
            marker=dict(
                size=6,
                color='#FF6B6B',
                line=dict(width=0.5, color='white')
            ),
            hovertemplate='Altitud: %{x:.2f}m<br>Temperatura: %{y:.2f}°C<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Panel 4: Presión vs Altitud
    fig.add_trace(
        go.Scatter(
            x=altitud,
            y=presion,
            mode='markers',
            name='Presión',
            marker=dict(
                size=6,
                color='#0066FF',
                line=dict(width=0.5, color='white')
            ),
            hovertemplate='Altitud: %{x:.2f}m<br>Presión: %{y:.3f}hPa<extra></extra>'
        ),
        row=2, col=2
    )
    
    # Actualizar ejes
    fig.update_xaxes(title_text="Altitud (m)", row=1, col=1)
    fig.update_yaxes(title_text="Densidad (kg/m³)", row=1, col=1)
    
    fig.update_xaxes(title_text="Tiempo (s)", row=1, col=2)
    fig.update_yaxes(title_text="Densidad (kg/m³)", row=1, col=2)
    
    fig.update_xaxes(title_text="Altitud (m)", row=2, col=1)
    fig.update_yaxes(title_text="Temperatura (°C)", row=2, col=1)
    
    fig.update_xaxes(title_text="Altitud (m)", row=2, col=2)
    fig.update_yaxes(title_text="Presión (hPa)", row=2, col=2)
    
    # Estilo general
    fig.update_layout(
        title={
            'text': "<b>ANÁLISIS DE DENSIDAD AERODINÁMICA</b><br><sub>Ecuación: ρ = P / (R × T)</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1f77b4'}
        },
        hovermode='closest',
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=11),
        height=900,
        showlegend=True,
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1)
    )
    
    return fig

def main():
    print("\n" + "="*70)
    print("  SCRIPT 3: ANÁLISIS DE DENSIDAD AERODINÁMICA")
    print("="*70)
    
    print("\n✓ Cargando datos...")
    df, presion_pa, temp_k = cargar_datos()
    print(f"  → {len(df)} puntos de datos cargados")
    
    print("\n✓ Calculando densidad del aire...")
    print("  Ecuación: ρ = P / (R × T)")
    print("  • R = 287.05 J/(kg·K)")
    print("  • P = Presión en Pa")
    print("  • T = Temperatura en K")
    
    densidad = calcular_densidad(presion_pa, temp_k)
    
    print(f"\n  Estadísticas de densidad:")
    print(f"  • Media: {densidad.mean():.6f} kg/m³")
    print(f"  • Máxima: {densidad.max():.6f} kg/m³")
    print(f"  • Mínima: {densidad.min():.6f} kg/m³")
    print(f"  • Desv. Est.: {densidad.std():.6f} kg/m³")
    
    print("\n✓ Generando gráfica interactiva...")
    fig = crear_grafica_interactiva(df, densidad)
    
    # Guardar HTML
    archivo_html = Path(__file__).parent / "03_densidad_aerodinamica.html"
    fig.write_html(str(archivo_html))
    print(f"  → Gráfica guardada en: {archivo_html}")
    
    # Abrir en navegador
    print("\n✓ Abriendo en navegador...")
    webbrowser.open(f'file://{archivo_html.absolute()}')
    
    print("\n" + "="*70)
    print("  ✓ ANÁLISIS COMPLETADO")
    print("="*70)
    
    print("\n" + "="*70)
    print("  EXPLICACIÓN: CÓMO LA DENSIDAD AFECTA LA AERODINÁMICA")
    print("="*70)
    
    print("""
1. RESISTENCIA AERODINÁMICA (ARRASTRE)
   ─────────────────────────────────────
   • La fuerza de arrastre depende DIRECTAMENTE de la densidad:
     D = 0.5 × ρ × v² × Cd × A
   
   • A MAYOR densidad (bajo en la atmósfera):
     ✓ Mayor resistencia, mayor desaceleración
     ✓ El cohete consume más energía para mantener velocidad
   
   • A MENOR densidad (en el apogeo):
     ✓ Menor resistencia, menos pérdida de energía
     ✓ El cohete puede alcanzar mayor altitud

2. NÚMERO DE REYNOLDS Y RÉGIMEN DE FLUJO
   ──────────────────────────────────────
   • Re = (ρ × v × D) / μ
   
   • A BAJA densidad (altitud alta):
     ✓ Re disminuye → Flujo más laminar
     ✓ Menor coeficiente de arrastre (Cd)
   
   • A ALTA densidad (baja altitud):
     ✓ Re alto → Flujo turbulento
     ✓ Mayor coeficiente de arrastre (Cd)

3. DESPLIEGUE DEL PARACAÍDAS
   ──────────────────────────
   • El paracaídas necesita DENSIDAD SUFICIENTE para funcionar
   
   • Fuerza de frenado: F = 0.5 × ρ × v² × Cd × A
   
   • Si se despliega a altitud muy alta (ρ muy baja):
     ✗ Frenado insuficiente
   
   • Altitud óptima: 500-1000m donde ρ ≈ 1.0-1.1 kg/m³

4. VELOCIDAD TERMINAL
   ──────────────────
   • vt = √(2mg / (ρ Cd A))
   
   • A mayor ρ → menor velocidad terminal
   • A menor ρ → mayor velocidad terminal
   • Crítico en la fase de descenso

5. ESTABILIDAD Y CONTROL
   ─────────────────────
   • Fuerzas laterales ∝ ρ
   
   • Mayor densidad → mejor control de aletas
   • Menor densidad → trayectoria menos predecible
    """)
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
