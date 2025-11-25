import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ================================
# 1️⃣ Leer JSON
# ================================
with open("DATOSHpaFixed.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# ================================
# 2️⃣ Calcular altura real (BMP280)
# ================================
P0 = df["presion"].iloc[0]
df["altura_m"] = 55330 * (1 - (df["presion"] / P0) ** (1 / 5.255))
df.loc[df["altura_m"] < 0, "altura_m"] = 0

df["tiempo_s"] = df["tiempo_ms"] / 1000

# ================================
# 3️⃣ Detectar TODOS los despegues por grupos
# ================================
# 1. Detectamos saltos fuertes como "candidatos de despegue"
df["diff"] = df["altura_m"].diff()
indices_despegue = df[df["diff"] > 2.0].index.tolist()

# 2. Clasificamos cada vuelo usando la separación entre saltos (> 1s)
vuelos_indices = []
vuelo_actual = [indices_despegue[0]]

for idx in indices_despegue[1:]:
    if df.loc[idx, "tiempo_s"] - df.loc[vuelo_actual[-1], "tiempo_s"] > 1.0:
        vuelos_indices.append(vuelo_actual)
        vuelo_actual = [idx]
    else:
        vuelo_actual.append(idx)
vuelos_indices.append(vuelo_actual)

# ================================
# 4️⃣ Extraer EXACTAMENTE los 3 vuelos usando ms (sin basura)
# ================================

vuelos = []
# despegues = [2318, 4295, 6573]
despegues = [2319, 4322, 6620]
# despegues = [group[0] for group in vuelos_indices[:3]]  # índices detectados del salto

for i in range(3):

    idx_despegue = despegues[i]

    # --- 1. Inicio: 200 ms antes del despegue ---
    inicio_ms = df.loc[idx_despegue, "tiempo_ms"] - 200
    if inicio_ms < 0:
        inicio_ms = 0

    # --- 2. Fin real: altura < 0.5 m durante 200 ms ---
    ventana_ms = 200
    fin_real_idx = None

    for j in range(idx_despegue, len(df)):
        t_actual = df.loc[j, "tiempo_ms"]
        t_fin_ventana = t_actual + ventana_ms

        tramo = df[(df["tiempo_ms"] >= t_actual) &
                   (df["tiempo_ms"] <= t_fin_ventana)]

        if (tramo["altura_m"] < 0.5).all():
            fin_real_idx = j
            break

    # si no detecta fin, usar final del dataset
    if fin_real_idx is None:
        fin_real_idx = df.index[-1]

    # --- 3. Recortar exactamente el vuelo ---
    vuelo_df = df[(df["tiempo_ms"] >= inicio_ms) &
                  (df.index <= fin_real_idx)].copy()

    # Quitar ruido o ceros antes/después
    vuelo_df = vuelo_df[vuelo_df["altura_m"] > 0.05].copy()

    if vuelo_df.empty:
        continue

    # --- 4. Normalizar tiempo relativo (en segundos) ---
    vuelo_df["t_rel"] = (vuelo_df["tiempo_ms"] - vuelo_df["tiempo_ms"].iloc[0]) / 1000.0

    vuelos.append(vuelo_df.reset_index(drop=True))


# ================================
# 5️⃣ Alturas teóricas
# ================================
tiempos_vuelo = [3.0, 3.5, 4.0]
alturas_teoricas = [1.225 * t**2 for t in tiempos_vuelo]

# ================================
# 6️⃣ Graficar TODOS los vuelos juntos
# ================================
plt.figure(figsize=(14, 8))

# ================================
# 6️⃣ Gráficos SEPARADOS por vuelo en UNA sola ventana (con valores dentro del gráfico)
# ================================

colores = ["green", "blue", "orange"]
colores_teo = ["red", "purple", "black"]
labels = ["Vuelo 1", "Vuelo 2", "Vuelo 3"]

# plt.figure(figsize=(14, 12))

for i in range(3):
    vuelo_df = vuelos[i]

    # Calcular altura real del vuelo
    altura_real_max = vuelo_df["altura_m"].max()

    # Altura teórica
    altura_teo = alturas_teoricas[i]

    # Error entre altura teórica y real
    error = altura_teo - altura_real_max

    plt.subplot(3, 1, i + 1)

    # Curva real
    plt.plot(
        vuelo_df["t_rel"],
        vuelo_df["altura_m"],
        color=colores[i],
        linewidth=2,
        label=f"{labels[i]} - Altura Real: {altura_real_max:.2f} m"
    )

    # Línea teórica
    plt.axhline(
        altura_teo,
        linestyle="--",
        color=colores_teo[i],
        linewidth=2,
        label=f"Altura Teórica ({altura_teo:.2f} m)"
    )

    plt.plot(
        altura_teo,
        linestyle="-",
        color="#0000",
        linewidth=2,
        label=f"Error: {error:.2f} m"
    )

    plt.title(f"{labels[i]} - Altura Real vs Altura Teórica")
    plt.xlabel("Tiempo relativo (s)")
    plt.ylabel("Altura (m)")
    plt.grid(True)
    plt.legend(loc="upper right")

plt.tight_layout()
plt.show()

# ================================
# 📌 Curvas Altitud vs Presión + Error Promedio
# ================================

plt.figure(figsize=(14, 12))

for i in range(3):
    vuelo_df = vuelos[i]

    # Datos reales
    P_real = vuelo_df["presion"]
    h_real = vuelo_df["altura_m"]

    # Presión base del vuelo
    P0 = P_real.iloc[0]

    # Curva teórica usando P_real
    h_teo_realP = 44330 * (1 - (P_real / P0) ** 0.1903)

    # Curva teórica ordenada (suavizada)
    h_teo = np.linspace(h_real.min(), h_real.max(), 200)
    P_teo = P0 * (1 - (h_teo / 44330)) ** 5.255

    # Error punto a punto
    error_i = h_real - h_teo_realP
    error_prom = np.mean(np.abs(error_i))

    plt.subplot(3, 1, i + 1)

    # ============================
    # Curva real
    plt.plot(
        P_real, h_real,
        color="blue",
        linewidth=2,
        label="Curva Real (Sensor)"
    )

    # Curva teórica
    plt.plot(
        P_teo, h_teo,
        color="red",
        linestyle="--",
        linewidth=2,
        label="Curva Teórica (Ecuación Barométrica)"
    )

    plt.plot(
        P_teo, h_teo,
        color="#0000",
        linestyle="-",
        linewidth=2,
        label=f"Error promedio: {error_prom:.2f} m"
    )

    plt.title(f"Vuelo {i+1}: Altitud vs Presión")
    plt.xlabel("Presión (hPa)")
    plt.ylabel("Altitud (m)")
    plt.grid(True)
    plt.legend(loc="best")

plt.tight_layout()
plt.show()
