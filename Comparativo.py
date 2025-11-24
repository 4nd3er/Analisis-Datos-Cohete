import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# — Asumiendo que ya tienes tu df con vuelo: df_vuelo
# — Supongamos que tienes otro DataFrame: df_clima
#   con columnas: 'hora_local', 'presion_clima', 'temperatura_clima'.

# Convertir hora_local a un eje numérico si necesario
df_clima['hora_ms'] = (pd.to_datetime(df_clima['hora_local']) 
                       - pd.to_datetime(df_clima['hora_local'].min())).dt.total_seconds()*1000

fig = make_subplots(rows=2, cols=1, shared_xaxes=False,
                    subplot_titles=("Presión: Vuelo vs Ambiente", "Temperatura: Vuelo vs Ambiente"))

# Presión: vuelo
fig.add_trace(go.Scatter(x=df_vuelo['tiempo_ms'], y=df_vuelo['presion'],
                         name='Presión Vuelo', line=dict(color='blue')), row=1, col=1)
# Presión: ambiente
fig.add_trace(go.Scatter(x=df_clima['hora_ms'], y=df_clima['presion_clima'],
                         name='Presión Ambiente', line=dict(color='red', dash='dash')), row=1, col=1)

# Temperatura: vuelo
fig.add_trace(go.Scatter(x=df_vuelo['tiempo_ms'], y=df_vuelo['temperatura'],
                         name='Temp Vuelo', line=dict(color='green')), row=2, col=1)
# Temperatura: ambiente
fig.add_trace(go.Scatter(x=df_clima['hora_ms'], y=df_clima['temperatura_clima'],
                         name='Temp Ambiente', line=dict(color='orange', dash='dash')), row=2, col=1)

fig.update_layout(title="Comparativo Vuelo vs Clima (Piendamó noche 1 Nov 2025)",
                  height=700, hovermode="x unified")
fig.update_xaxes(title_text="Tiempo ms (vuelo) / Hora relativa (ambiente)")

fig.show()
