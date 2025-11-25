import json
import pandas as pd
import matplotlib.pyplot as plt

# ============================
# 1. Cargar datos JSON
# ============================

# Si tu sensor exporta un JSON en archivo, usa:
with open("DATOSHpaFixed.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# ============================
# 2. Altitud real desde presión (BMP280)
#    Fórmula barométrica estándar
# ============================

P0 = 101325      # Presión a nivel del mar (Pa)
TEMP = 288.15    # Temperatura estándar (K)
g = 9.80665      # gravedad
R = 287.05       # constante de gas del aire

df["alt_real"] = ( (P0 / df["presion"])**(1/5.257) - 1 ) * TEMP / 0.0065

# ============================
# 3. Altitud teórica usando ecuación barométrica
# ============================

df["alt_teorica"] = ( (P0 / df["presion"])**(1/5.257) - 1 ) * TEMP / 0.0065

# ============================
# 4. Graficar curva de altitud vs presión
# ============================

plt.figure(figsize=(10,6))
plt.plot(df["presion"], df["alt_real"], marker='o', label="Altitud Real (BMP280)")
plt.plot(df["presion"], df["alt_teorica"], marker='x', linestyle='--', label="Altitud Teórica (Ecuación Barométrica)")

plt.xlabel("Presión (Pa)")
plt.ylabel("Altitud (m)")
plt.title("Comparación Altitud vs Presión - Sensor BMP280 vs Ecuación Barométrica")
plt.legend()
plt.grid(True)
plt.gca().invert_xaxis()   # Presión baja = altitud alta
plt.show()

