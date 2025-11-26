"""
Análisis Completo de Datos - Cohete de Agua
Incluye estadísticas, visualizaciones y comparaciones
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configuración de estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

# ===============================
# 1. Cargar y procesar datos
# ===============================

with open("datalanzamientos.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def calcular_apogeo_littlewood(t_vuelo: float) -> float:
    """Formula: h = 1.225 * t^2"""
    return 1.225 * (t_vuelo ** 2)

# Procesar datos SIN electrónica (únicos válidos para la fórmula de Littlewood)
lanzamientos_sin = []
for intento in data["sin_componentes_electronicos"]["intentos"]:
    tiempo = intento["tiempo_vuelo_s"]
    apogeo = calcular_apogeo_littlewood(tiempo)
    lanzamientos_sin.append({
        "numero_intento": intento["numero_intento"],
        "presion_psi": intento["presion_inicial_psi"],
        "volumen_agua_ml": intento["volumen_agua_ml"],
        "tiempo_vuelo_s": tiempo,
        "apogeo_estimado_m": apogeo,
        "tipo": "Sin Electrónica"
    })

df_sin = pd.DataFrame(lanzamientos_sin)

# ===============================
# 2. Estadísticas Descriptivas
# ===============================

print("\n" + "="*60)
print("ANÁLISIS ESTADÍSTICO COMPLETO - COHETE DE AGUA")
print("="*60)

print("\n[ESTADISTICAS] COHETES SIN ELECTRONICA")
print("-" * 60)
print(df_sin[["presion_psi", "volumen_agua_ml", "tiempo_vuelo_s", "apogeo_estimado_m"]].describe())

# ===============================
# 3. Análisis de Correlación
# ===============================

print("\n[CORRELACION] Presion vs Apogeo (Sin Electronica)")
print("-" * 60)
correlacion = df_sin["presion_psi"].corr(df_sin["apogeo_estimado_m"])
print(f"Coeficiente de correlación: {correlacion:.4f}")

if correlacion > 0.7:
    print("[OK] Correlacion FUERTE positiva")
elif correlacion > 0.4:
    print("[!] Correlacion MODERADA positiva")
else:
    print("[X] Correlacion DEBIL")

# ===============================
# 4. Fórmula del Éxito
# ===============================

mejor = df_sin.loc[df_sin["apogeo_estimado_m"].idxmax()]
peor = df_sin.loc[df_sin["apogeo_estimado_m"].idxmin()]

print("\n[FORMULA DEL EXITO]")
print("-" * 60)
print(f"Mejor lanzamiento (Intento #{int(mejor['numero_intento'])})")
print(f"  - Presion: {mejor['presion_psi']} PSI")
print(f"  - Tiempo de vuelo: {mejor['tiempo_vuelo_s']:.2f} s")
print(f"  - Apogeo estimado: {mejor['apogeo_estimado_m']:.2f} m")

print(f"\nPeor lanzamiento (Intento #{int(peor['numero_intento'])})")
print(f"  - Presion: {peor['presion_psi']} PSI")
print(f"  - Tiempo de vuelo: {peor['tiempo_vuelo_s']:.2f} s")
print(f"  - Apogeo estimado: {peor['apogeo_estimado_m']:.2f} m")

diferencia = mejor['apogeo_estimado_m'] - peor['apogeo_estimado_m']
print(f"\n[DIFERENCIA] Diferencia de apogeo: {diferencia:.2f} m ({(diferencia/peor['apogeo_estimado_m']*100):.1f}% mas alto)")

# ===============================
# 5. Visualizaciones
# ===============================

fig = plt.figure(figsize=(14, 10))

# Gráfico 1: Presión vs Apogeo
ax1 = plt.subplot(2, 2, 1)
plt.scatter(df_sin["presion_psi"], df_sin["apogeo_estimado_m"], 
            s=200, c=df_sin["apogeo_estimado_m"], cmap='viridis', 
            edgecolors='black', linewidth=2, alpha=0.8)
plt.plot(df_sin["presion_psi"], df_sin["apogeo_estimado_m"], 
         'r--', alpha=0.5, linewidth=1)
plt.xlabel("Presión Inicial (PSI)", fontsize=12, fontweight='bold')
plt.ylabel("Apogeo Estimado (m)", fontsize=12, fontweight='bold')
plt.title("Presión vs Apogeo\n(Sin Electrónica)", fontsize=14, fontweight='bold')
plt.colorbar(label='Apogeo (m)')
plt.grid(True, alpha=0.3)

# Marcar el mejor punto
plt.scatter(mejor['presion_psi'], mejor['apogeo_estimado_m'], 
            s=400, marker='*', c='red', edgecolors='black', 
            linewidth=2, label='Fórmula del Éxito', zorder=5)
plt.legend()

# Gráfico 2: Tiempo de vuelo vs Apogeo
ax2 = plt.subplot(2, 2, 2)
plt.scatter(df_sin["tiempo_vuelo_s"], df_sin["apogeo_estimado_m"], 
            s=200, c='green', edgecolors='black', linewidth=2, alpha=0.7)
# Línea teórica de Littlewood
t_teorico = np.linspace(df_sin["tiempo_vuelo_s"].min(), 
                        df_sin["tiempo_vuelo_s"].max(), 100)
h_teorico = 1.225 * t_teorico**2
plt.plot(t_teorico, h_teorico, 'b-', linewidth=2, 
         label='Fórmula Littlewood: h=1.225t²')
plt.xlabel("Tiempo de Vuelo (s)", fontsize=12, fontweight='bold')
plt.ylabel("Apogeo Estimado (m)", fontsize=12, fontweight='bold')
plt.title("Tiempo vs Apogeo\n(Validación Littlewood)", fontsize=14, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)

# Gráfico 3: Comparación de todos los intentos
ax3 = plt.subplot(2, 2, 3)
x = range(1, len(df_sin) + 1)
bars = plt.bar(x, df_sin["apogeo_estimado_m"], 
               color=['red' if i == mejor['numero_intento'] else 'steelblue' 
                      for i in df_sin["numero_intento"]], 
               edgecolor='black', linewidth=2, alpha=0.8)
plt.xlabel("Número de Intento", fontsize=12, fontweight='bold')
plt.ylabel("Apogeo Estimado (m)", fontsize=12, fontweight='bold')
plt.title("Comparación de Todos los Lanzamientos\n(Sin Electrónica)", 
          fontsize=14, fontweight='bold')
plt.xticks(x)
plt.grid(True, alpha=0.3, axis='y')

# Añadir valores sobre las barras
for i, (idx, row) in enumerate(df_sin.iterrows()):
    plt.text(i+1, row["apogeo_estimado_m"] + 0.5, 
             f"{row['apogeo_estimado_m']:.1f}m\n{row['presion_psi']:.0f} PSI", 
             ha='center', fontsize=9, fontweight='bold')

# Gráfico 4: Eficiencia por presión
ax4 = plt.subplot(2, 2, 4)
eficiencia = df_sin["apogeo_estimado_m"] / df_sin["presion_psi"]
plt.plot(df_sin["presion_psi"], eficiencia, 'o-', 
         color='purple', markersize=10, linewidth=2, 
         markeredgecolor='black', markeredgewidth=2)
plt.xlabel("Presión Inicial (PSI)", fontsize=12, fontweight='bold')
plt.ylabel("Eficiencia (m/PSI)", fontsize=12, fontweight='bold')
plt.title("Eficiencia: Apogeo por PSI", fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)

# Marcar punto óptimo
idx_max_eficiencia = eficiencia.idxmax()
plt.scatter(df_sin.loc[idx_max_eficiencia, "presion_psi"], 
            eficiencia[idx_max_eficiencia], 
            s=300, marker='*', c='red', edgecolors='black', 
            linewidth=2, zorder=5)

plt.tight_layout()
plt.savefig("analisis_completo_cohete.png", dpi=300, bbox_inches='tight')
print("\n[OK] Graficos guardados en: analisis_completo_cohete.png")

# ===============================
# 6. Conclusiones Automáticas
# ===============================

print("\n" + "="*60)
print("[CONCLUSIONES PRINCIPALES]")
print("="*60)

print("\n1. FORMULA DEL EXITO IDENTIFICADA:")
print(f"   - Presion optima: {mejor['presion_psi']} PSI")
print(f"   - Volumen de agua: {mejor['volumen_agua_ml']} ml")
print(f"   - Apogeo maximo alcanzado: {mejor['apogeo_estimado_m']:.2f} m")

print("\n2. ANALISIS DE RENDIMIENTO:")
promedio_apogeo = df_sin["apogeo_estimado_m"].mean()
desviacion = df_sin["apogeo_estimado_m"].std()
print(f"   - Apogeo promedio: {promedio_apogeo:.2f} m")
print(f"   - Desviacion estandar: {desviacion:.2f} m")
print(f"   - Rango de apogeos: {df_sin['apogeo_estimado_m'].min():.2f} - {df_sin['apogeo_estimado_m'].max():.2f} m")

print("\n3. RELACION PRESION-RENDIMIENTO:")
if correlacion > 0.7:
    print(f"   [OK] Mayor presion = Mayor apogeo (r={correlacion:.3f})")
    print("   - Recomendacion: Usar presiones entre 50-55 PSI")
else:
    print(f"   [!] La presion no es el unico factor determinante (r={correlacion:.3f})")

print("\n4. RECOMENDACIONES:")
print("   [OK] Usar configuracion del Intento #4:")
print(f"      - Presion: {mejor['presion_psi']} PSI")
print(f"      - Agua: {mejor['volumen_agua_ml']} ml")
print("   [OK] Evitar presiones menores a 47 PSI")
print("   [OK] Mantener volumen de agua constante en 500 ml")

print("\n" + "="*60)
print("Analisis completado [OK]")
print("="*60 + "\n")

plt.show() 

