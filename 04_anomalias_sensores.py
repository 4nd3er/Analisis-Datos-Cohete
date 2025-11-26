"""
SCRIPT 4: DETECCIÓN DE ANOMALÍAS EN DATOS DEL COHETE
=====================================================
Detecta anomalías (picos o caídas bruscas) usando:
- Z-score: Desviación estándar
- IQR (Interquartile Range): Rango intercuartílico

Clasifica posibles causas:
- Ruido de sensor
- Vibración del cohete
- Interferencia electromagnética
- Cambios físicos legítimos
"""

import json
import pandas as pd
import numpy as np
from scipy import stats
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
    
    # Calcular altitud
    P0 = 101325
    T0 = 288.15
    g = 9.81
    R = 287.05
    
    presion_pa = df['presion'] * 100
    temp_k = df['temperatura'] + 273.15
    
    h = (T0 / 0.0065) * ((presion_pa / P0) ** (-0.0065 * R / g) - 1)
    df['altitud'] = h
    
    return df

def detectar_anomalias_zscore(datos, umbral=3):
    """
    Detecta anomalías usando Z-score
    Z = (x - media) / desv_estandar
    
    Si |Z| > umbral: es una anomalía
    """
    media = np.mean(datos)
    desv = np.std(datos)
    
    z_scores = np.abs((datos - media) / desv)
    anomalias = z_scores > umbral
    
    return anomalias, z_scores

def detectar_anomalias_iqr(datos, factor=1.5):
    """
    Detecta anomalías usando IQR (Rango Intercuartílico)
    
    Q1 = 25% percentil
    Q3 = 75% percentil
    IQR = Q3 - Q1
    
    Anomalía si: x < Q1 - 1.5×IQR o x > Q3 + 1.5×IQR
    """
    Q1 = np.percentile(datos, 25)
    Q3 = np.percentile(datos, 75)
    IQR = Q3 - Q1
    
    limite_inferior = Q1 - factor * IQR
    limite_superior = Q3 + factor * IQR
    
    anomalias = (datos < limite_inferior) | (datos > limite_superior)
    
    return anomalias, limite_inferior, limite_superior

def clasificar_anomalia(idx, datos, tiempo, coluna_name):
    """
    Clasifica la posible causa de una anomalía
    """
    
    # Análisis de contexto
    if idx > 0 and idx < len(datos) - 1:
        cambio = abs(datos[idx] - datos[idx-1])
        cambio_siguiente = abs(datos[idx+1] - datos[idx])
    else:
        cambio = abs(datos[idx] - np.mean(datos))
        cambio_siguiente = cambio
    
    magnitud = abs(datos[idx] - np.mean(datos))
    desv = np.std(datos)
    
    # Razones de anomalía
    razones = []
    probabilidades = {}
    
    # 1. Ruido de sensor (cambio muy rápido y puntual)
    if cambio > desv * 2 and cambio_siguiente < desv:
        probabilidades['Ruido de Sensor'] = 0.8
        razones.append("Cambio abrupto y aislado")
    
    # 2. Vibración (oscilaciones pequeñas frecuentes)
    if 0.1 < magnitud < 0.5 * desv:
        probabilidades['Vibración'] = 0.7
        razones.append("Magnitud pequeña pero distinta")
    
    # 3. Interferencia electromagnética (patrón irregular)
    if magnitud > desv * 3:
        probabilidades['Interferencia EMI'] = 0.6
        razones.append("Anomalía muy pronunciada")
    
    # 4. Cambio físico legítimo (cambio gradual)
    if cambio < desv * 0.5 and cambio_siguiente < desv * 0.5:
        probabilidades['Cambio Físico'] = 0.9
        razones.append("Transición suave")
    
    # Categorizar por tipo de variable
    if coluna_name == 'temperatura':
        if magnitud > desv * 2:
            probabilidades['Cambio en Altitud'] = 0.7
    elif coluna_name == 'presion':
        if magnitud > desv * 2:
            probabilidades['Cambio de Fase'] = 0.8
    
    # Si no hay clasificación clara
    if not probabilidades:
        probabilidades['Desconocida'] = 0.5
    
    # Ordenar por probabilidad
    causa_principal = max(probabilidades, key=probabilidades.get)
    
    return causa_principal, probabilidades, razones

def crear_grafica_anomalias(df, col_analizar, anomalias_zscore, anomalias_iqr):
    """
    Crea gráfica interactiva mostrando anomalías
    """
    
    tiempo = df['tiempo_s'].values
    datos = df[col_analizar].values
    
    # Detectar indices de anomalías
    anomalias_combinadas = anomalias_zscore | anomalias_iqr
    indices_anomalias = np.where(anomalias_combinadas)[0]
    
    # Colores según método de detección
    colores = []
    for i in range(len(datos)):
        if anomalias_zscore[i] and anomalias_iqr[i]:
            colores.append('#FF0000')  # Rojo: ambos métodos
        elif anomalias_zscore[i]:
            colores.append('#FF8C00')  # Naranja: Z-score
        elif anomalias_iqr[i]:
            colores.append('#FFD700')  # Amarillo: IQR
        else:
            colores.append('#0066FF')  # Azul: normal
    
    # Crear figura
    fig = go.Figure()
    
    # Datos normales
    normal_mask = ~anomalias_combinadas
    fig.add_trace(go.Scatter(
        x=tiempo[normal_mask],
        y=datos[normal_mask],
        mode='markers',
        name='Datos Normales',
        marker=dict(size=6, color='#0066FF', opacity=0.6),
        hovertemplate='Tiempo: %{x:.2f}s<br>Valor: %{y:.3f}<extra></extra>'
    ))
    
    # Anomalías detectadas por ambos métodos
    ambos_mask = anomalias_zscore & anomalias_iqr
    if np.any(ambos_mask):
        fig.add_trace(go.Scatter(
            x=tiempo[ambos_mask],
            y=datos[ambos_mask],
            mode='markers',
            name='Anomalía (Z-score + IQR)',
            marker=dict(size=12, color='#FF0000', symbol='diamond', line=dict(width=2, color='darkred')),
            hovertemplate='<b>ANOMALÍA</b><br>Tiempo: %{x:.2f}s<br>Valor: %{y:.3f}<extra></extra>'
        ))
    
    # Anomalías solo Z-score
    solo_zscore = anomalias_zscore & ~anomalias_iqr
    if np.any(solo_zscore):
        fig.add_trace(go.Scatter(
            x=tiempo[solo_zscore],
            y=datos[solo_zscore],
            mode='markers',
            name='Anomalía (Z-score)',
            marker=dict(size=10, color='#FF8C00', symbol='circle', line=dict(width=1, color='darkorange')),
            hovertemplate='<b>ANOMALÍA (Z-score)</b><br>Tiempo: %{x:.2f}s<br>Valor: %{y:.3f}<extra></extra>'
        ))
    
    # Anomalías solo IQR
    solo_iqr = anomalias_iqr & ~anomalias_zscore
    if np.any(solo_iqr):
        fig.add_trace(go.Scatter(
            x=tiempo[solo_iqr],
            y=datos[solo_iqr],
            mode='markers',
            name='Anomalía (IQR)',
            marker=dict(size=10, color='#FFD700', symbol='square', line=dict(width=1, color='goldenrod')),
            hovertemplate='<b>ANOMALÍA (IQR)</b><br>Tiempo: %{x:.2f}s<br>Valor: %{y:.3f}<extra></extra>'
        ))
    
    # Línea de tendencia
    fig.add_trace(go.Scatter(
        x=tiempo,
        y=datos,
        mode='lines',
        name='Tendencia',
        line=dict(color='rgba(100,100,100,0.3)', width=1),
        hoverinfo='skip'
    ))
    
    # Estadísticas
    media = np.mean(datos)
    desv = np.std(datos)
    
    fig.add_hline(y=media, line_dash="dash", line_color="green", annotation_text="Media")
    fig.add_hline(y=media + 3*desv, line_dash="dot", line_color="orange", annotation_text="±3σ (Z-score)")
    fig.add_hline(y=media - 3*desv, line_dash="dot", line_color="orange")
    
    # Actualizar layout
    fig.update_layout(
        title={
            'text': f"<b>DETECCIÓN DE ANOMALÍAS: {col_analizar.upper()}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#1f77b4'}
        },
        xaxis_title="Tiempo (segundos)",
        yaxis_title=f"{col_analizar} (unidades)",
        hovermode='x unified',
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        height=600,
        showlegend=True,
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.9)', bordercolor='black', borderwidth=1)
    )
    
    return fig, indices_anomalias

def main():
    print("\n" + "="*70)
    print("  SCRIPT 4: DETECCIÓN DE ANOMALÍAS EN DATOS DEL COHETE")
    print("="*70)
    
    print("\n✓ Cargando datos...")
    df = cargar_datos()
    print(f"  → {len(df)} puntos de datos cargados")
    
    # Columnas a analizar
    columnas = ['temperatura', 'presion']
    
    # Crear subplots
    figs_html = []
    
    for col in columnas:
        print(f"\n✓ Analizando {col}...")
        datos = df[col].values
        tiempo = df['tiempo_s'].values
        
        # Detectar anomalías
        anomalias_z, z_scores = detectar_anomalias_zscore(datos, umbral=2.5)
        anomalias_iqr, lim_inf, lim_sup = detectar_anomalias_iqr(datos, factor=1.5)
        
        anomalias_combinadas = anomalias_z | anomalias_iqr
        num_anomalias = np.sum(anomalias_combinadas)
        
        print(f"  • Anomalías (Z-score): {np.sum(anomalias_z)}")
        print(f"  • Anomalías (IQR): {np.sum(anomalias_iqr)}")
        print(f"  • Anomalías totales: {num_anomalias}")
        
        # Análisis de anomalías
        indices_anomalias = np.where(anomalias_combinadas)[0]
        
        if len(indices_anomalias) > 0:
            print(f"\n  Primeras 5 anomalías detectadas:")
            for i, idx in enumerate(indices_anomalias[:5]):
                causa, prob, razones = clasificar_anomalia(idx, datos, tiempo, col)
                print(f"    {i+1}. t={tiempo[idx]:.2f}s, valor={datos[idx]:.3f}")
                print(f"       → Causa probable: {causa} ({prob[causa]:.0%})")
                print(f"       → {', '.join(razones)}")
        
        # Generar gráfica
        print(f"\n  ✓ Generando gráfica para {col}...")
        fig, _ = crear_grafica_anomalias(df, col, anomalias_z, anomalias_iqr)
        
        # Guardar HTML
        archivo_html = Path(__file__).parent / f"04_anomalias_{col}.html"
        fig.write_html(str(archivo_html))
        figs_html.append(archivo_html)
        print(f"    → Guardada en: {archivo_html}")
    
    # Abrir en navegador
    print("\n✓ Abriendo gráficas en navegador...")
    for archivo in figs_html:
        webbrowser.open(f'file://{archivo.absolute()}')
    
    print("\n" + "="*70)
    print("  TIPOS DE ANOMALÍAS Y CAUSAS POSIBLES")
    print("="*70)
    
    print("""
1. RUIDO DE SENSOR
   ─────────────────
   • Características:
     - Cambios muy rápidos y puntuales
     - Recuperación inmediata al valor anterior
     - Magnitud variable
   
   • Causas:
     - Interferencia electromagnética
     - Contacto defectuoso en sensor
     - Calibración incorrecta
   
   • Mitigation:
     - Usar filtros digitales (Kalman, Butterworth)
     - Blindaje electromagnético
     - Verificar conexiones

2. VIBRACIÓN DEL COHETE
   ─────────────────────
   • Características:
     - Oscilaciones pequeñas y repetitivas
     - Frecuencia cercana a resonancia del cohete
     - Amplitud crece en fases de aceleración
   
   • Causas:
     - Motor en funcionamiento
     - Inestabilidad aerodinámica
     - Turbuleneia en el aire
   
   • Análisis:
     - FFT para detectar frecuencia dominante
     - Esperado: 10-100 Hz

3. INTERFERENCIA ELECTROMAGNÉTICA (EMI)
   ────────────────────────────────────
   • Características:
     - Picos aislados muy grandes
     - Sin patrón obvio
     - Afecta múltiples sensores simultáneamente
   
   • Causas:
     - Radiación RF cercana
     - Encendido/apagado de equipos
     - Transitorios de potencia
   
   • Solución:
     - Filtros RC
     - Puesta a tierra adecuada

4. CAMBIOS FÍSICOS LEGÍTIMOS
   ──────────────────────────
   • Características:
     - Transición suave
     - Correlación con otras variables
     - Magnitud consistente
   
   • Ejemplos:
     - Cambio de altitud → caída de presión
     - Despliegue de paracaídas → aceleración
     - Cambios en flujo de aire → temperatura
   
   • Validación:
     - Correlacionar variables
     - Comprobar con acelerómetro
     - Análisis temporal
    """)
    
    print("\n" + "="*70)
    print("  ✓ ANÁLISIS COMPLETADO")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
