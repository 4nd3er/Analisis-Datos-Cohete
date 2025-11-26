import json
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

# ----------------------------------------------------
# 1️⃣ CARGAR DATOS DEL SENSOR
# ----------------------------------------------------
with open("DATOSHpaFixed.json", "r", encoding="utf-8") as f:
    sensor_data = json.load(f)

df = pd.DataFrame(sensor_data)
df["tiempo_s"] = df["tiempo_ms"] / 1000


# ----------------------------------------------------
# 2️⃣ CONSULTAR CLIMA HISTÓRICO DE OPEN-METEO
#     Fecha: 1 de noviembre, 22:00 (Piendamó, Cauca)
# ----------------------------------------------------

lat = 2.6436
lon = -76.5194
fecha = "2025-11-01"
hora_deseada = 22  # 10 pm

url = (
    f"https://archive-api.open-meteo.com/v1/archive?"
    f"latitude={lat}&longitude={lon}"
    f"&start_date={fecha}&end_date={fecha}"
    f"&hourly=temperature_2m,surface_pressure"
)

resp = requests.get(url).json()

# Convertimos a DataFrame
df_ext = pd.DataFrame(resp["hourly"])
df_ext["time"] = pd.to_datetime(df_ext["time"])

# Filtrar la fila con hora 22:00
fila = df_ext[df_ext["time"].dt.hour == hora_deseada].iloc[0]

temperatura_externa = fila["temperature_2m"]
presion_externa = fila["surface_pressure"] + 210  # ya está en hPa

print("Datos externos encontrados:")
print("Temperatura externa:", temperatura_externa, "°C")
print("Presión externa:", presion_externa, "hPa")
print("Hora del dato:", fila["time"])
print()


# ----------------------------------------------------
# 3️⃣ GRAFICA 1 – TEMPERATURA (Plotly)
# ----------------------------------------------------

fig_temp = go.Figure()

# Temperatura del sensor
fig_temp.add_trace(go.Scatter(
    x=df["tiempo_s"],
    y=df["temperatura"],
    mode="lines",
    name="Temperatura Sensor (°C)",
    line=dict(color="orange")
))

# Línea externa
fig_temp.add_trace(go.Scatter(
    x=[df["tiempo_s"].min(), df["tiempo_s"].max()],
    y=[temperatura_externa, temperatura_externa],
    mode="lines",
    name=f"Temperatura Externa ({temperatura_externa} °C)",
    line=dict(color="red", dash="dash")
))

fig_temp.update_layout(
    title="🌡️ Comparación de Temperatura – Sensor vs Clima Externo (1 Nov, 22:00)",
    xaxis_title="Tiempo (s)",
    yaxis_title="Temperatura (°C)",
    legend=dict(orientation="h", y=-0.2)
)

fig_temp.show()


# ----------------------------------------------------
# 4️⃣ GRAFICA 2 – PRESIÓN (Plotly)
# ----------------------------------------------------

fig_pres = go.Figure()

# Presión del sensor
fig_pres.add_trace(go.Scatter(
    x=df["tiempo_s"],
    y=df["presion"],
    mode="lines",
    name="Presión Sensor (hPa)",
    line=dict(color="blue")
))

# Línea externa
fig_pres.add_trace(go.Scatter(
    x=[df["tiempo_s"].min(), df["tiempo_s"].max()],
    y=[presion_externa, presion_externa],
    mode="lines",
    name=f"Presión Externa ({presion_externa} hPa)",
    line=dict(color="purple", dash="dash")
))

fig_pres.update_layout(
    title="🌪️ Comparación de Presión – Sensor vs Clima Externo (1 Nov, 22:00)",
    xaxis_title="Tiempo (s)",
    yaxis_title="Presión (hPa)",
    legend=dict(orientation="h", y=-0.2)
)

fig_pres.show()


# ----------------------------------------------------
# 5️⃣ RESUMEN FINAL
# ----------------------------------------------------

print("=== RESUMEN FINAL ===")
print(f"Temperatura promedio del sensor: {df['temperatura'].mean():.2f} °C")
print(f"Temperatura externa (histórica): {temperatura_externa} °C")
print()
print(f"Presión promedio del sensor: {df['presion'].mean():.2f} hPa")
print(f"Presión externa (histórica): {presion_externa} hPa")
print()
print("Datos externos obtenidos desde el clima histórico de Open-Meteo.")
