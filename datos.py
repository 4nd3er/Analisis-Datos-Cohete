import json
import pandas as pd
import matplotlib.pyplot as plt

# --- 1️⃣ Leer el JSON corregido ---
with open("DATOSHpa.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# --- 2️⃣ Calcular la altura usando la fórmula barométrica ---
P0 = df["presion"].iloc[0]  # presión inicial como referencia
df["altura_m"] = 44330 * (1 - (df["presion"] / P0) ** (1 / 5.255))

# --- 3️⃣ Corregir valores negativos ---
df.loc[df["altura_m"] < 0, "altura_m"] = 0

# --- 4️⃣ Guardar el nuevo archivo con altura corregida ---
df.to_json("DATOS_finales_altura.json", orient="records", indent=2, force_ascii=False)

# --- 5️⃣ Calcular mínimos y máximos ---
stats = {
    "Temperatura (°C)": (df["temperatura"].min(), df["temperatura"].max()),
    "Presión (hPa)": (df["presion"].min(), df["presion"].max()),
    "Altura (m)": (df["altura_m"].min(), df["altura_m"].max())
}

# --- 6️⃣ Mostrar en consola ---
print("\n--- ESTADÍSTICAS ---")
for key, (min_val, max_val) in stats.items():
    print(f"{key}:")
    print(f"  → Mínimo: {min_val:.2f}")
    print(f"  → Máximo: {max_val:.2f}\n")

# --- 7️⃣ Crear las gráficas ---
plt.figure(figsize=(12, 10))

# a) Temperatura vs tiempo
plt.subplot(3, 1, 1)
plt.plot(df["tiempo_ms"] / 1000, df["temperatura"], color="orange")
plt.title("Temperatura vs Tiempo")
plt.xlabel("Tiempo (s)")
plt.ylabel("Temperatura (°C)")
plt.grid(True)
plt.text(0.02, 0.95, f"Min: {stats['Temperatura (°C)'][0]:.2f}°C\nMax: {stats['Temperatura (°C)'][1]:.2f}°C",
         transform=plt.gca().transAxes, fontsize=10, bbox=dict(facecolor='white', alpha=0.6))

# b) Presión vs tiempo
plt.subplot(3, 1, 2)
plt.plot(df["tiempo_ms"] / 1000, df["presion"], color="blue")
plt.title("Presión vs Tiempo")
plt.xlabel("Tiempo (s)")
plt.ylabel("Presión (hPa)")
plt.grid(True)
plt.text(0.02, 0.95, f"Min: {stats['Presión (hPa)'][0]:.2f} hPa\nMax: {stats['Presión (hPa)'][1]:.2f} hPa",
         transform=plt.gca().transAxes, fontsize=10, bbox=dict(facecolor='white', alpha=0.6))

# c) Altura vs tiempo
plt.subplot(3, 1, 3)
plt.plot(df["tiempo_ms"] / 1000, df["altura_m"], color="green")
plt.title("Altura estimada vs Tiempo (BMP280 - Vuelo del cohete)")
plt.xlabel("Tiempo (s)")
plt.ylabel("Altura (m)")
plt.grid(True)
plt.text(0.02, 0.95, f"Min: {stats['Altura (m)'][0]:.2f} m\nMax: {stats['Altura (m)'][1]:.2f} m",
         transform=plt.gca().transAxes, fontsize=10, bbox=dict(facecolor='white', alpha=0.6))

plt.tight_layout()
plt.show()

# --- 8️⃣ Mostrar resumen del vuelo ---
print(f"Altura máxima: {df['altura_m'].max():.2f} m")
print(f"Duración total del registro: {df['tiempo_ms'].iloc[-1] / 1000:.2f} s")
