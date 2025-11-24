import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import numpy as np

# --- 1️⃣ Leer y procesar el archivo ---
with open("DATOS_finales_corregido.json", "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(r'\]\s*\[', ',', text.strip())
if not text.strip().startswith('['):
    text = '[' + text
if not text.strip().endswith(']'):
    text = text + ']'

data = json.loads(text)
df = pd.DataFrame(data)

df['tiempo_ms'] = pd.to_numeric(df['tiempo_ms'], errors='coerce')
df['temperatura'] = pd.to_numeric(df['temperatura'], errors='coerce')
df['presion'] = pd.to_numeric(df['presion'], errors='coerce')

# Calcular altitud (si no existe)
P0 = 1013.25  # Presión de referencia (hPa) - ajusta si es diferente
df['altitud'] = 44330 * (1 - (df['presion'] / P0)**(1/5.255))  # En metros

# Agregar vuelo_id si no existe (asume uno; cambia si hay múltiples)
if 'vuelo_id' not in df.columns:
    df['vuelo_id'] = 1

# --- 2️⃣ Crear la gráfica 1: Altitud, Presión y Temperatura vs. Tiempo ---
fig1 = make_subplots(
    rows=3, cols=1, shared_xaxes=True,
    subplot_titles=("Altitud (m) vs. Tiempo (ms)", "Presión (hPa) vs. Tiempo (ms)", "Temperatura (°C) vs. Tiempo (ms)"),
    vertical_spacing=0.1
)

# Colores por vuelo para diferenciación
colores = ['blue', 'red', 'green', 'orange']  # Agrega más si hay más vuelos

for i, vuelo in enumerate(df['vuelo_id'].unique()):
    df_vuelo = df[df['vuelo_id'] == vuelo]
    color = colores[i % len(colores)]
    
    # Altitud
    fig1.add_trace(go.Scatter(
        x=df_vuelo['tiempo_ms'], y=df_vuelo['altitud'],
        mode='lines', name=f'Altitud Vuelo {vuelo}', line=dict(color=color, width=2),
        hovertemplate='Tiempo: %{x} ms<br>Altitud: %{y:.2f} m'
    ), row=1, col=1)
    
    # Presión
    fig1.add_trace(go.Scatter(
        x=df_vuelo['tiempo_ms'], y=df_vuelo['presion'],
        mode='lines', name=f'Presión Vuelo {vuelo}', line=dict(color=color, dash='dot', width=2),
        hovertemplate='Tiempo: %{x} ms<br>Presión: %{y:.2f} hPa'
    ), row=2, col=1)
    
    # Temperatura
    fig1.add_trace(go.Scatter(
        x=df_vuelo['tiempo_ms'], y=df_vuelo['temperatura'],
        mode='lines', name=f'Temperatura Vuelo {vuelo}', line=dict(color=color, dash='dash', width=2),
        hovertemplate='Tiempo: %{x} ms<br>Temperatura: %{y:.2f} °C'
    ), row=3, col=1)

# Configurar layout
# --- Configurar layout (ajuste en update_xaxes) ---
fig1.update_layout(
    title="Gráfica 1: Altitud, Presión y Temperatura vs. Tiempo por Vuelo",
    height=900,
    hovermode="x unified",
    legend_title="Vuelos"
)
# Mostrar título del eje X en TODOS los subplots
fig1.update_xaxes(title_text="Tiempo (ms)", row=1, col=1)
fig1.update_xaxes(title_text="Tiempo (ms)", row=2, col=1)
fig1.update_xaxes(title_text="Tiempo (ms)", row=3, col=1)
fig1.update_yaxes(title_text="Altitud (m)", row=1, col=1)
fig1.update_yaxes(title_text="Presión (hPa)", row=2, col=1)
fig1.update_yaxes(title_text="Temperatura (°C)", row=3, col=1)

# Mostrar gráfica
fig1.show()

# Guardar como HTML
fig1.write_html('grafica1_altitud_presion_temperatura.html')
print("✅ Gráfica 1 guardada como 'grafica1_altitud_presion_temperatura.html'")
