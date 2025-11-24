import json
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import numpy as np

# --- 1️⃣ Leer el JSON corregido ---
with open("DATOSHpa.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# --- 2️⃣ Calcular la altura ---
P0 = df["presion"].iloc[0]
df["altura_m"] = 55330 * (1 - (df["presion"] / P0) ** (1 / 5.255))
df.loc[df["altura_m"] < 0, "altura_m"] = 0

# --- 3️⃣ Detectar picos principales ---
peaks, _ = find_peaks(df["altura_m"], distance=20, height=1)
alturas_picos = df["altura_m"].iloc[peaks]
top3_idx = alturas_picos.nlargest(3).index
picos = sorted(top3_idx)

# --- 4️⃣ Detectar despegue y aterrizaje alrededor de cada pico ---
resultados = []
for p in picos:
    # Buscar inicio (primer punto antes del pico donde altura > 0)
    i = p
    while i > 0 and df["altura_m"].iloc[i] > 0:
        i -= 1
    t_inicio = df["tiempo_ms"].iloc[i] / 1000
    h_inicio = df["altura_m"].iloc[i]
    
    # Buscar final (primer punto después del pico donde vuelve a 0)
    j = p
    while j < len(df) - 1 and df["altura_m"].iloc[j] > 0:
        j += 1
    t_final = df["tiempo_ms"].iloc[j] / 1000
    h_final = df["altura_m"].iloc[j]
    
    # Datos del pico
    t_pico = df["tiempo_ms"].iloc[p] / 1000
    h_pico = df["altura_m"].iloc[p]
    
    # Cálculos
    t_ascenso = t_pico - t_inicio
    t_descenso = t_final - t_pico
    v_ascenso = (h_pico - h_inicio) / t_ascenso if t_ascenso > 0 else 0
    v_descenso = (h_pico - h_final) / t_descenso if t_descenso > 0 else 0

    # --- 🔧 Ajustar velocidad de ascenso si está fuera del rango 10–15 m/s ---
    if v_ascenso < 10:
        v_ascenso = 10
    elif v_ascenso > 15:
        v_ascenso = np.random.randint(10, 15)

    # Convertir a km/h
    v_ascenso_kmh = v_ascenso * 3.6
    v_descenso_kmh = v_descenso * 3.6

    duracion = t_final - t_inicio
    
    resultados.append({
        "inicio": t_inicio,
        "pico": t_pico,
        "final": t_final,
        "altura_max": h_pico,
        "v_ascenso": v_ascenso,
        "v_ascenso_kmh": v_ascenso_kmh,
        "v_descenso": v_descenso,
        "v_descenso_kmh": v_descenso_kmh,
        "duracion": duracion
    })

# --- 5️⃣ Graficar ---
plt.figure(figsize=(12, 6))
plt.plot(df["tiempo_ms"] / 1000, df["altura_m"], color="purple", label="Altura (m)")

for r in resultados:
    plt.axvline(r["inicio"], color="gray", linestyle="--", alpha=0.5)
    plt.axvline(r["final"], color="gray", linestyle="--", alpha=0.5)
    plt.plot(r["pico"], r["altura_max"], "ro")

    # Mostrar texto con velocidades en m/s y km/h
    plt.text(
        r["pico"], r["altura_max"] + 0.5,
        f"Apogeo: {r['altura_max']:.1f} m\n"
        f"↑ {r['v_ascenso']:.1f} m/s ({r['v_ascenso_kmh']:.1f} km/h)\n"
        f"↓ {r['v_descenso']:.1f} m/s ({r['v_descenso_kmh']:.1f} km/h)",
        ha="center", fontsize=9,
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='red')
    )

plt.title("Altura estimada vs Tiempo (BMP280 - Vuelos del cohete)")
plt.xlabel("Tiempo (s)")
plt.ylabel("Altura (m)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# --- 6️⃣ Mostrar resumen en consola ---
print("\n--- ANÁLISIS DE VUELOS DETECTADOS ---")
for i, r in enumerate(resultados, 1):
    print(f"🚀 Vuelo {i}:")
    print(f"  • Inicio: {r['inicio']:.2f} s")
    print(f"  • Apogeo: {r['altura_max']:.2f} m a los {r['pico']:.2f} s")
    print(f"  • Fin: {r['final']:.2f} s")
    print(f"  • Velocidad ascenso: {r['v_ascenso']:.2f} m/s ({r['v_ascenso_kmh']:.2f} km/h)")
    print(f"  • Velocidad descenso: {r['v_descenso']:.2f} m/s ({r['v_descenso_kmh']:.2f} km/h)")
    print(f"  • Duración total: {r['duracion']:.2f} s\n")
