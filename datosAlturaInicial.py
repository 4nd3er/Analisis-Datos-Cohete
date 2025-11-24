import json
import pandas as pd
import matplotlib.pyplot as plt

# Leer el JSON corregido
with open("DATOS.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Convertir a DataFrame
df = pd.DataFrame(data)

# Calcular altura (referencia: presión inicial)
P0 = df["presion"].iloc[0]
df["altura_m"] = 44330 * (1 - (df["presion"] / P0) ** (1 / 5.255))

# Guardar nuevo archivo con la altura
df.to_json("DATOS_finales_altura.json", orient="records", indent=2, force_ascii=False)

# Graficar
plt.figure(figsize=(10, 5))
plt.plot(df["tiempo_ms"] / 1000, df["altura_m"], label="Altura estimada")
plt.title("Altura estimada vs Tiempo (BMP280 - Vuelo del cohete)")
plt.xlabel("Tiempo (s)")
plt.ylabel("Altura (m)")
plt.grid(True)
plt.legend()
plt.show()

# Mostrar datos clave
print(f"Altura máxima: {df['altura_m'].max():.2f} m")
print(f"Duración total del registro: {df['tiempo_ms'].iloc[-1] / 1000:.2f} s")
