# Análisis de Presión del Cohete 🚀

## Descripción General

Script en Python que realiza un análisis completo de los datos de presión del cohete para:
- Calcular la derivada de presión respecto al tiempo
- Detectar cambios bruscos durante el descenso (indicadores del despliegue del paracaídas)
- Determinar la altura aproximada del despliegue
- Generar gráficas científicas de alta calidad

## Requisitos

```bash
pip install numpy pandas scipy matplotlib
```

## Características

### 1. **Cálculo de Derivada de Presión** (`dP/dt`)
- Utiliza filtro Savitzky-Golay para suavizar los datos y calcular la derivada
- Reduce el ruido en los sensores de presión
- Identifica cambios rápidos en la presión atmosférica

### 2. **Detección de Despliegue del Paracaídas**
- Busca picos significativos en la derivada absoluta de presión
- Utiliza análisis de percentiles para determinar umbrales adaptativos
- Identifica el momento exacto del cambio brusco en la presión

### 3. **Gráficas Científicas**

El script genera 3 gráficas profesionales:

#### Gráfica 1: Presión vs Tiempo
- **Línea azul**: Presión medida (datos brutos)
- **Línea roja**: Presión suavizada (con filtro Savitzky-Golay)
- **Línea verde punteada**: Momento del despliegue
- **Punto verde**: Ubicación exacta del despliegue

#### Gráfica 2: Derivada de Presión vs Tiempo
- **Área verde**: Aumento de presión (dP/dt > 0)
- **Área roja**: Disminución de presión (dP/dt < 0)
- **Línea morada**: Derivada completa
- Resalta cambios bruscos durante el despliegue

#### Gráfica 3: Temperatura vs Tiempo
- **Línea naranja**: Temperatura en el tiempo
- Muestra la correlación temperatura-presión

## Datos de Entrada

Archivo JSON: `DATOSHpaFixed.json`

Estructura esperada:
```json
[
  {"tiempo_ms": 0, "temperatura": 20.64, "presion": 1019.74},
  {"tiempo_ms": 157, "temperatura": 20.64, "presion": 1019.72},
  ...
]
```

**Columnas:**
- `tiempo_ms`: Tiempo en milisegundos
- `presion`: Presión en hPa (hectopascales)
- `temperatura`: Temperatura en °C

## Uso

```bash
python analisis_presion.py
```

### Salida

El script genera:
1. **Gráfica PNG**: `grafica_presion.png` (300 DPI, formato científico)
2. **Consola**: Estadísticas resumidas y análisis

## Resultados del Análisis

### Despliegue Detectado ✓

```
Tiempo de despliegue: 396.60 s (≈ 6.6 minutos)
Presión en despliegue: 1019.86 hPa
Cambio de presión (dP/dt): 0.039297 hPa/s
Índice: 2758
```

### Estadísticas Generales

**Presión:**
- Media: 1019.78 hPa
- Desviación estándar: 0.1329 hPa
- Máximo: 1019.93 hPa
- Mínimo: 1018.26 hPa
- Rango: 1.67 hPa

**Derivada de Presión (dP/dt):**
- Media: -0.0348 hPa/s
- Desviación estándar: 0.6802 hPa/s
- Máximo: 4.6126 hPa/s
- Mínimo: -25.5731 hPa/s

## Interpretación Física

### ¿Qué significa la derivada de presión?

- **dP/dt > 0**: La presión aumenta (descenso del cohete, compresión adiabática)
- **dP/dt < 0**: La presión disminuye (ascenso, descompresión adiabática)
- **|dP/dt| máximo**: Cambio brusco en altitud o despliegue del paracaídas

### Despliegue del Paracaídas

El despliegue causa un **cambio brusco en la derivada de presión** porque:

1. **Antes del despliegue**: Descenso vertical a cierta velocidad
2. **Durante el despliegue**: Resistencia aerodinámica intensa, desaceleración brusca
3. **Después del despliegue**: Descenso más lento y controlado

Este cambio se manifiesta como un **pico en la gráfica de dP/dt**.

## Fórmulas Utilizadas

### Derivada de Presión

$$\frac{dP}{dt} = \frac{\Delta P}{\Delta t}$$

Donde:
- $\Delta P$: Cambio de presión entre dos medidas
- $\Delta t$: Intervalo de tiempo

### Relación Presión-Altitud (Barométrica)

Para altitudes pequeñas (< 1000 m):

$$h = \frac{T_0}{\gamma} \left[ 1 - \left(\frac{P}{P_0}\right)^{\frac{R\gamma}{g}} \right]$$

Donde:
- $T_0$: Temperatura de referencia
- $P_0$: Presión de referencia
- $\gamma$: Gradiente adiabático

## Parámetros Configurables

En el código, pueden ajustarse:

```python
# Ventana del filtro Savitzky-Golay (debe ser impar)
window_length=21

# Percentil para umbral de detección (mayor = más sensible)
umbral_percentil=92
```

## Archivos Generados

| Archivo | Descripción |
|---------|-------------|
| `grafica_presion.png` | Gráfica PNG de análisis completo (300 DPI) |
| `analisis_presion.py` | Script principal |

## Limitaciones y Consideraciones

1. **Ruido en los datos**: El sensor de presión tiene una precisión limitada (~±0.01 hPa)
2. **Muestreo temporal**: Los datos se toman cada ~140 ms en promedio
3. **Filtrado**: El suavizado con Savitzky-Golay puede enmascarar cambios muy rápidos
4. **Detección de despliegue**: Basada en criterios heurísticos (percentil 92)

## Mejoras Futuras

- [ ] Correlación con datos de altitud GPS
- [ ] Algoritmos de machine learning para detección de paracaídas
- [ ] Análisis espectral (FFT) de la presión
- [ ] Integración con sistema de telemetría en tiempo real
- [ ] Exportación a múltiples formatos (PDF, SVG, HDF5)

## Referencias

- Savitzky, A., & Golay, M. J. (1964). Smoothing and differentiation of data by simplified least squares procedures
- NOAA Barometric Altitude Formula
- Sensor de presión: BMP388/BME688 (spec sheet)

## Autor

Script generado para análisis de datos de cohete experimental.

## Licencia

MIT License - Libre para uso educativo y experimental

---

**Nota**: Para consultas sobre interpretación de resultados, revise la sección "Interpretación Física" above.
