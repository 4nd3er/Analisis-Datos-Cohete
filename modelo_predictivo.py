import json
import numpy as np
import sys

def cargar_datos():
    try:
        with open("datalanzamientos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["sin_componentes_electronicos"]["intentos"]
    except FileNotFoundError:
        print("Error: No se encontró el archivo datalanzamientos.json")
        sys.exit(1)

def calcular_apogeo_littlewood(t_vuelo):
    # h = 1.225 * t^2
    return 1.225 * (t_vuelo ** 2)

def entrenar_modelo(intentos):
    presiones = []
    apogeos = []

    print("\n[ENTRENAMIENTO] Procesando datos históricos...")
    for intento in intentos:
        p = intento["presion_inicial_psi"]
        t = intento["tiempo_vuelo_s"]
        h = calcular_apogeo_littlewood(t)
        
        presiones.append(p)
        apogeos.append(h)
        print(f"  - Intento #{intento['numero_intento']}: {p} PSI -> {h:.2f} m")

    X = np.array(presiones)
    y = np.array(apogeos)

    # Ajuste polinómico de grado 2 (parábola) ya que la física sugiere rendimientos decrecientes o curvas
    # Aunque con pocos datos, una lineal también serviría, pero grado 2 es más flexible.
    coeficientes = np.polyfit(X, y, 2)
    modelo = np.poly1d(coeficientes)
    
    print(f"\n[MODELO] Modelo generado: Polinomio de grado 2")
    print(f"  - Ecuación: {coeficientes[0]:.4f}*x^2 + {coeficientes[1]:.4f}*x + {coeficientes[2]:.4f}")
    
    return modelo

def simular(modelo):
    print("\n" + "="*50)
    print("   SIMULADOR DE LANZAMIENTO - PREDICCIÓN DE APOGEO")
    print("="*50)
    print("Escribe 'salir' para terminar.\n")

    while True:
        entrada = input(">> Ingresa la Presión (PSI): ")
        
        if entrada.lower() == 'salir':
            print("Cerrando simulador...")
            break
        
        try:
            presion = float(entrada)
            if presion < 0:
                print("Error: La presión no puede ser negativa.")
                continue
                
            prediccion = modelo(presion)
            
            print(f"\n   [RESULTADO]")
            print(f"   Para una presión de {presion} PSI:")
            print(f"   -> Altura estimada: {prediccion:.2f} metros")
            
            # Advertencias de seguridad/rango
            if presion > 80:
                print("   [!] ADVERTENCIA: Presión muy alta, riesgo de explosión de la botella.")
            elif presion < 20:
                print("   [!] Nota: Presión baja, el vuelo será corto.")
            print("-" * 30 + "\n")
            
        except ValueError:
            print("Error: Por favor ingresa un número válido.")

if __name__ == "__main__":
    datos = cargar_datos()
    modelo = entrenar_modelo(datos)
    simular(modelo)
