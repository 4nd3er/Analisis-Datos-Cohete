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
    
    # Usar presión para estimar altitud relativa (sin normalizar aún)
    P0 = 101325  # Pa
    T0 = 288.15  # K
    g = 9.81
    R = 287.05
    
    presion_pa = df['presion'] * 100  # Convertir hPa a Pa
    temp_k = df['temperatura'] + 273.15
    
    h_relativa = (T0 / 0.0065) * ((presion_pa / P0) ** (-0.0065 * R / g) - 1)
    
    # Normalizar a rango 0-1 primero
    h_min = h_relativa.min()
    h_max = h_relativa.max()
    h_rango = h_max - h_min
    
    if h_rango != 0:
        df['altitud_raw'] = ((h_relativa - h_min) / h_rango)
    else:
        df['altitud_raw'] = 0.5
    
    # Guardar también para referencia (antes de normalización final)
    df['altitud'] = df['altitud_raw'].copy()
    
    return df

def detectar_fases(df, ventana=151):
    """
    Detecta las tres fases del vuelo eliminando ruido
    - Ascenso: altitud aumentando
    - Apogeo: máxima altitud
    - Descenso: altitud disminuyendo
    
    Nota: La normalización a 13.98m se hace DESPUÉS del suavizado
    para garantizar que el máximo sea exactamente 13.98m
    """
    
    altitud = df['altitud'].values  # Altitud normalizada 0-1
    altitud_maxima_real = 13.98  # Altura máxima real en metros
    
    # Suavizar agresivamente para eliminar ruido (ventana más grande)
    if len(altitud) > ventana:
        # Aplicar múltiples pasadas de suavizado
        altitud_suavizada = savgol_filter(altitud, ventana, 3)
        altitud_suavizada = savgol_filter(altitud_suavizada, ventana, 3)
    else:
        altitud_suavizada = altitud
    
    # NORMALIZAR A 13.98m DESPUÉS del suavizado
    # Escalar el máximo suavizado para que sea exactamente 13.98m
    # Esto preserva la forma de la curva pero garantiza el máximo correcto
    max_suavizado = np.max(altitud_suavizada)
    if max_suavizado > 0:
        factor_escala = altitud_maxima_real / max_suavizado
        altitud_suavizada_metros = altitud_suavizada * factor_escala
    else:
        altitud_suavizada_metros = altitud_suavizada * altitud_maxima_real
    
    # Calcular derivada (cambio de altitud)
    derivada = np.gradient(altitud_suavizada_metros)
    
    # Encontrar apogeo (máxima altitud)
    idx_apogeo = np.argmax(altitud_suavizada_metros)
    
    # Detectar fases con histéresis para evitar falsos cambios
    fases = []
    fase_actual = None
    idx_cambio_fase = []
    
    # Aplicar umbral para ignorar pequeños cambios (ruido)
    umbral = 0.0001
    derivada_filtrada = np.where(np.abs(derivada) > umbral, derivada, 0)
    
    for i in range(len(derivada_filtrada) - 1):
        if derivada_filtrada[i] > umbral:  # Ascenso
            nueva_fase = 'Ascenso'
        elif derivada_filtrada[i] < -umbral:  # Descenso
            nueva_fase = 'Descenso'
        else:
            nueva_fase = fase_actual
        
        if nueva_fase != fase_actual:
            fase_actual = nueva_fase
            idx_cambio_fase.append(i)
            fases.append(nueva_fase)
    
    return altitud_suavizada_metros, derivada, idx_apogeo, idx_cambio_fase, fases

def crear_grafica_interactiva(df, altitud_suavizada, derivada, idx_apogeo, idx_cambio_fase):
    """
    Crea 6 gráficas separadas analizando diferentes fases del vuelo
    """
    
    tiempo = df['tiempo_real'].values
    n_puntos = len(tiempo)
    
    # Dividir en fases: 2 ascenso, 1 apogeo, 3 descenso
    idx_ascenso_fin = idx_apogeo
    idx_ascenso_1_fin = int(idx_ascenso_fin * 0.5)  # Primer 50% del ascenso
    idx_ascenso_2_fin = idx_ascenso_fin  # Segundo 50% del ascenso
    
    # Descenso dividido en 3 partes iguales
    idx_descenso_inicio = idx_apogeo
    idx_descenso_largo = n_puntos - idx_descenso_inicio
    idx_descenso_1_fin = idx_descenso_inicio + int(idx_descenso_largo * 0.33)
    idx_descenso_2_fin = idx_descenso_inicio + int(idx_descenso_largo * 0.67)
    idx_descenso_3_fin = n_puntos
    
    # Crear figura con 6 subplots (2 filas x 3 columnas)
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=(
            "Ascenso Fase 1", "Ascenso Fase 2", "Apogeo (Punto Máximo)",
            "Descenso Fase 1", "Descenso Fase 2", "Descenso Fase 3"
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # Colores para cada fase
    colores = {
        'ascenso_1': '#00CC44',
        'ascenso_2': '#00AA44',
        'apogeo': '#FFD700',
        'descenso_1': '#FF8866',
        'descenso_2': '#FF6B6B',
        'descenso_3': '#CC5555'
    }
    
    # FILA 1 - ASCENSO Y APOGEO
    # Ascenso Fase 1
    fig.add_trace(
        go.Scatter(
            x=tiempo[:idx_ascenso_1_fin],
            y=altitud_suavizada[:idx_ascenso_1_fin],
            mode='lines',
            name='Ascenso 1',
            line=dict(color=colores['ascenso_1'], width=3),
            hovertemplate='<b>Ascenso Fase 1</b><br>Tiempo: %{x:.2f}s<br>Altitud: %{y:.2f}m<extra></extra>'
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=tiempo[:idx_ascenso_1_fin],
            y=derivada[:idx_ascenso_1_fin],
            mode='lines',
            name='Velocidad 1',
            line=dict(color='#0066FF', width=2),
            hovertemplate='Velocidad: %{y:.3f}m/s<extra></extra>',
            visible='legendonly'
        ),
        row=1, col=1
    )
    
    # Ascenso Fase 2
    fig.add_trace(
        go.Scatter(
            x=tiempo[idx_ascenso_1_fin:idx_ascenso_2_fin],
            y=altitud_suavizada[idx_ascenso_1_fin:idx_ascenso_2_fin],
            mode='lines',
            name='Ascenso 2',
            line=dict(color=colores['ascenso_2'], width=3),
            hovertemplate='<b>Ascenso Fase 2</b><br>Tiempo: %{x:.2f}s<br>Altitud: %{y:.2f}m<extra></extra>'
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=tiempo[idx_ascenso_1_fin:idx_ascenso_2_fin],
            y=derivada[idx_ascenso_1_fin:idx_ascenso_2_fin],
            mode='lines',
            name='Velocidad 2',
            line=dict(color='#0066FF', width=2),
            hovertemplate='Velocidad: %{y:.3f}m/s<extra></extra>',
            visible='legendonly'
        ),
        row=1, col=2
    )
    
    # Apogeo
    fig.add_trace(
        go.Scatter(
            x=tiempo[max(0, idx_apogeo-5):min(len(tiempo), idx_apogeo+5)],
            y=altitud_suavizada[max(0, idx_apogeo-5):min(len(tiempo), idx_apogeo+5)],
            mode='lines+markers',
            name='Apogeo',
            line=dict(color=colores['apogeo'], width=3),
            marker=dict(size=8),
            hovertemplate='<b>Apogeo</b><br>Tiempo: %{x:.2f}s<br>Altitud: %{y:.2f}m<extra></extra>'
        ),
        row=1, col=3
    )
    fig.add_trace(
        go.Scatter(
            x=[tiempo[idx_apogeo]],
            y=[altitud_suavizada[idx_apogeo]],
            mode='markers+text',
            name='Máximo',
            marker=dict(size=15, color=colores['apogeo'], symbol='star', line=dict(color='#FF8C00', width=2)),
            text=[f"{altitud_suavizada[idx_apogeo]:.2f}m"],
            textposition="top center",
            hovertemplate='<b>MÁXIMA ALTITUD</b><br>Tiempo: %{x:.2f}s<br>Altitud: %{y:.2f}m<extra></extra>'
        ),
        row=1, col=3
    )
    
    # FILA 2 - DESCENSO
    # Descenso Fase 1
    fig.add_trace(
        go.Scatter(
            x=tiempo[idx_descenso_inicio:idx_descenso_1_fin],
            y=altitud_suavizada[idx_descenso_inicio:idx_descenso_1_fin],
            mode='lines',
            name='Descenso 1',
            line=dict(color=colores['descenso_1'], width=3),
            hovertemplate='<b>Descenso Fase 1</b><br>Tiempo: %{x:.2f}s<br>Altitud: %{y:.2f}m<extra></extra>'
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=tiempo[idx_descenso_inicio:idx_descenso_1_fin],
            y=derivada[idx_descenso_inicio:idx_descenso_1_fin],
            mode='lines',
            name='Velocidad Desc1',
            line=dict(color='#0066FF', width=2),
            hovertemplate='Velocidad: %{y:.3f}m/s<extra></extra>',
            visible='legendonly'
        ),
        row=2, col=1
    )
    
    # Descenso Fase 2
    fig.add_trace(
        go.Scatter(
            x=tiempo[idx_descenso_1_fin:idx_descenso_2_fin],
            y=altitud_suavizada[idx_descenso_1_fin:idx_descenso_2_fin],
            mode='lines',
            name='Descenso 2',
            line=dict(color=colores['descenso_2'], width=3),
            hovertemplate='<b>Descenso Fase 2</b><br>Tiempo: %{x:.2f}s<br>Altitud: %{y:.2f}m<extra></extra>'
        ),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=tiempo[idx_descenso_1_fin:idx_descenso_2_fin],
            y=derivada[idx_descenso_1_fin:idx_descenso_2_fin],
            mode='lines',
            name='Velocidad Desc2',
            line=dict(color='#0066FF', width=2),
            hovertemplate='Velocidad: %{y:.3f}m/s<extra></extra>',
            visible='legendonly'
        ),
        row=2, col=2
    )
    
    # Descenso Fase 3
    fig.add_trace(
        go.Scatter(
            x=tiempo[idx_descenso_2_fin:idx_descenso_3_fin],
            y=altitud_suavizada[idx_descenso_2_fin:idx_descenso_3_fin],
            mode='lines',
            name='Descenso 3',
            line=dict(color=colores['descenso_3'], width=3),
            hovertemplate='<b>Descenso Fase 3</b><br>Tiempo: %{x:.2f}s<br>Altitud: %{y:.2f}m<extra></extra>'
        ),
        row=2, col=3
    )
    fig.add_trace(
        go.Scatter(
            x=tiempo[idx_descenso_2_fin:idx_descenso_3_fin],
            y=derivada[idx_descenso_2_fin:idx_descenso_3_fin],
            mode='lines',
            name='Velocidad Desc3',
            line=dict(color='#0066FF', width=2),
            hovertemplate='Velocidad: %{y:.3f}m/s<extra></extra>',
            visible='legendonly'
        ),
        row=2, col=3
    )
    
    # Actualizar ejes
    for row in [1, 2]:
        for col in [1, 2, 3]:
            fig.update_xaxes(title_text="Tiempo (s)", row=row, col=col)
            fig.update_yaxes(title_text="Altitud (m)", row=row, col=col)
    
    # Estilo general
    fig.update_layout(
        title={
            'text': "<b>ANÁLISIS DETALLADO DE 6 FASES DE VUELO DEL COHETE</b><br><sub>Altura máxima real: 13.98 m | Tiempo total: 4 segundos</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1f77b4'}
        },
        hovermode='x unified',
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=11),
        height=900,
        showlegend=True,
        legend=dict(x=1.02, y=0.5, bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1)
    )
    
    # Crear HTML personalizado con explicaciones
    html_content = fig.to_html(include_plotlyjs='cdn')
    
    # Agregar explicaciones después de la gráfica
    explicaciones = """
    <div style="font-family: Arial, sans-serif; max-width: 1400px; margin: 30px auto; padding: 20px;">
        <h2 style="color: #1f77b4; border-bottom: 3px solid #1f77b4; padding-bottom: 10px;">📊 Explicación de las 6 Fases de Vuelo</h2>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            
            <!-- ASCENSO FASE 1 -->
            <div style="background: #E8F5E9; padding: 20px; border-radius: 8px; border-left: 5px solid #00CC44;">
                <h3 style="color: #00CC44; margin-top: 0;">🚀 Ascenso Fase 1 (Aceleración Inicial)</h3>
                <p><b>¿Qué sucede?</b></p>
                <ul>
                    <li>El cohete inicia su vuelo con máxima aceleración</li>
                    <li>La velocidad vertical aumenta rápidamente (positiva y creciente)</li>
                    <li>La altitud crece de forma acelerada</li>
                </ul>
                <p><b>Características observables:</b></p>
                <ul>
                    <li>Pendiente de altitud muy pronunciada</li>
                    <li>Derivada (velocidad) en su valor máximo positivo</li>
                    <li>Mayor consumo de combustible</li>
                </ul>
            </div>
            
            <!-- ASCENSO FASE 2 -->
            <div style="background: #E8F5E9; padding: 20px; border-radius: 8px; border-left: 5px solid #00AA44;">
                <h3 style="color: #00AA44; margin-top: 0;">📈 Ascenso Fase 2 (Desaceleración)</h3>
                <p><b>¿Qué sucede?</b></p>
                <ul>
                    <li>El cohete continúa subiendo pero pierde aceleración</li>
                    <li>La velocidad vertical disminuye (sigue siendo positiva pero menor)</li>
                    <li>La gravedad ejerce mayor influencia</li>
                </ul>
                <p><b>Características observables:</b></p>
                <ul>
                    <li>Pendiente de altitud menos pronunciada</li>
                    <li>Derivada positiva pero en descenso</li>
                    <li>Se acerca al punto de máxima altura</li>
                </ul>
            </div>
            
            <!-- APOGEO -->
            <div style="background: #FFF3E0; padding: 20px; border-radius: 8px; border-left: 5px solid #FFD700;">
                <h3 style="color: #FF8C00; margin-top: 0;">⭐ Apogeo (Punto Máximo)</h3>
                <p><b>¿Qué sucede?</b></p>
                <ul>
                    <li>La altitud alcanza su valor máximo: <b>13.98 metros</b></li>
                    <li>La velocidad vertical llega a CERO</li>
                    <li>El cohete cambia de dirección: de subida a bajada</li>
                </ul>
                <p><b>Características observables:</b></p>
                <ul>
                    <li>Pico máximo en la curva de altitud</li>
                    <li>Derivada cruza por cero</li>
                    <li>Punto de inflexión en la trayectoria</li>
                </ul>
            </div>
            
            <!-- DESCENSO FASE 1 -->
            <div style="background: #FFEBEE; padding: 20px; border-radius: 8px; border-left: 5px solid #FF8866;">
                <h3 style="color: #FF8866; margin-top: 0;">⬇️ Descenso Fase 1 (Aceleración Negativa)</h3>
                <p><b>¿Qué sucede?</b></p>
                <ul>
                    <li>El cohete comienza a caer desde el apogeo</li>
                    <li>La velocidad es negativa y aumenta en magnitud</li>
                    <li>La aceleración es máxima hacia abajo</li>
                </ul>
                <p><b>Características observables:</b></p>
                <ul>
                    <li>Altitud disminuye rápidamente</li>
                    <li>Derivada negativa y creciente en magnitud</li>
                    <li>Máxima velocidad de caída</li>
                </ul>
            </div>
            
            <!-- DESCENSO FASE 2 -->
            <div style="background: #FFEBEE; padding: 20px; border-radius: 8px; border-left: 5px solid #FF6B6B;">
                <h3 style="color: #FF6B6B; margin-top: 0;">📉 Descenso Fase 2 (Fase Media)</h3>
                <p><b>¿Qué sucede?</b></p>
                <ul>
                    <li>El cohete continúa cayendo con velocidad más estable</li>
                    <li>La velocidad es negativa pero su magnitud se estabiliza</li>
                    <li>Posible apertura de paracaídas o cambio aerodinámico</li>
                </ul>
                <p><b>Características observables:</b></p>
                <ul>
                    <li>Descenso moderado y más regular</li>
                    <li>Derivada negativa pero más estable</li>
                    <li>Cambio en la curva de descenso</li>
                </ul>
            </div>
            
            <!-- DESCENSO FASE 3 -->
            <div style="background: #FFEBEE; padding: 20px; border-radius: 8px; border-left: 5px solid #CC5555;">
                <h3 style="color: #CC5555; margin-top: 0;">🎯 Descenso Fase 3 (Fase Final/Aterrizaje)</h3>
                <p><b>¿Qué sucede?</b></p>
                <ul>
                    <li>El cohete se aproxima al suelo</li>
                    <li>La velocidad se reduce (menor magnitud negativa)</li>
                    <li>El paracaídas o frenado aerodinámico controla la caída</li>
                </ul>
                <p><b>Características observables:</b></p>
                <ul>
                    <li>Altitud cerca de cero</li>
                    <li>Derivada negativa pero con tendencia a cero</li>
                    <li>Impacto suave en el aterrizaje</li>
                </ul>
            </div>
        </div>
        
        <div style="background: #F5F5F5; padding: 20px; border-radius: 8px; margin-top: 30px; border: 2px solid #1f77b4;">
            <h3 style="color: #1f77b4; margin-top: 0;">💡 Conceptos Clave</h3>
            <ul>
                <li><b>Altitud (línea roja):</b> La altura sobre el suelo en metros</li>
                <li><b>Derivada/Velocidad Vertical (línea azul punteada):</b> La tasa de cambio de altitud (m/s)</li>
                <li><b>Valores positivos:</b> El cohete está subiendo</li>
                <li><b>Valores negativos:</b> El cohete está bajando</li>
                <li><b>Cero:</b> Momento exacto del apogeo (punto de inversión)</li>
            </ul>
        </div>
    </div>
    """
    
    # Insertar explicaciones antes del cierre del body
    html_content = html_content.replace('</body>', explicaciones + '</body>')
    
    return html_content

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
    print(f"  → Altitud máxima: {altitud_suavizada[idx_apogeo]:.2f}m")
    print(f"  → Número de cambios de fase detectados: {len(idx_cambio_fase)}")
    
    print("\n✓ Generando gráfica interactiva...")
    html_content = crear_grafica_interactiva(df, altitud_suavizada, derivada, idx_apogeo, idx_cambio_fase)
    
    # Guardar HTML
    archivo_html = Path(__file__).parent / "01_fases_vuelo.html"
    with open(str(archivo_html), 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  → Gráfica guardada en: {archivo_html}")
    
    # Abrir en navegador
    print("\n✓ Abriendo en navegador...")
    webbrowser.open(f'file://{archivo_html.absolute()}')
    
    print("\n" + "="*70)
    print("  ✓ ANÁLISIS COMPLETADO")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
