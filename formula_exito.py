# """
# Calculo de la Fórmula del Éxito - Cohete de Agua (SIN electrónica)
# Basado en la guía oficial - Método de Littlewood (h = 1.225 * t^2)

# Variables consideradas:
# - Presión inicial (PSI)
# - Volumen de agua (ml)
# - Tiempo de vuelo total (s)
# - Botella de 1.5L (volumen usable ≈ 500 ml recomendado)
# - Sin electrónica → menor masa → mayor apogeo
# """

# import json
# import pandas as pd

# # ===============================
# # 1. Cargar datos originales
# # ===============================

# with open("datalanzamientos.json", "r", encoding="utf-8") as f:
#     data = json.load(f)

# intentos_sin_elec = data["sin_componentes_electronicos"]["intentos"]

# # ===============================
# # 2. Procesar datos usando Littlewood
# # ===============================

# def calcular_apogeo_littlewood(t_vuelo: float) -> float:
#     """
#     Formula oficial de la guía:
#     h = 1.225 * t^2
#     Se usa SOLO para vuelos sin paracaídas.
#     """
#     return 1.225 * (t_vuelo ** 2)

# lanzamientos = []

# for intento in intentos_sin_elec:
#     tiempo = intento["tiempo_vuelo_s"]
#     apogeo = calcular_apogeo_littlewood(tiempo)

#     lanzamientos.append({
#         "numero_intento": intento["numero_intento"],
#         "presion_psi": intento["presion_inicial_psi"],
#         "volumen_agua_ml": intento["volumen_agua_ml"],
#         "tiempo_vuelo_s": tiempo,
#         "apogeo_estimado_m": apogeo
#     })

# df = pd.DataFrame(lanzamientos)

# # ===============================
# # 3. Determinar la Fórmula del Éxito
# # ===============================

# mejor = df.loc[df["apogeo_estimado_m"].idxmax()]

# print("\n==============================================")
# print("     FORMULA DEL ÉXITO - COHETE DE AGUA")
# print("     (Solo lanzamientos SIN electrónica)")
# print("==============================================")

# print(f"\nTotal de lanzamientos analizados: {len(df)}")
# print(f"Volumen de agua (constante): {df['volumen_agua_ml'].iloc[0]} ml")
# print(f"Botella usada: 1.5 litros")

# print("\n>> MEJOR COMBINACIÓN (Fórmula del Éxito):")
# print(f"   - Intento #{mejor['numero_intento']}")
# print(f"   - Presión inicial: {mejor['presion_psi']} PSI")
# print(f"   - Agua: {mejor['volumen_agua_ml']} ml")
# print(f"   - Tiempo de vuelo: {mejor['tiempo_vuelo_s']:.2f} s")
# print(f"   - Apogeo estimado: {mejor['apogeo_estimado_m']:.2f} m")

# # ===============================
# # 4. Guardar datos procesados
# # ===============================

# df.to_csv("resultados_formula_exito_sin_electronica.csv", index=False, encoding="utf-8")

# print("\n>> Archivo generado: resultados_formula_exito_sin_electronica.csv")
# print(">> Cálculo completado.\n")
