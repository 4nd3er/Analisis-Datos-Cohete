# Análisis de Densidad del Aire y Aerodinámica del Cohete 🚀

## Descripción

Script que calcula la **densidad del aire** usando la ecuación del gas ideal y analiza cómo impacta en la aerodinámica del cohete durante el vuelo.

## Ecuación del Gas Ideal

$$\rho = \frac{P}{R \cdot T}$$

Donde:
- **ρ** = densidad del aire (kg/m³)
- **P** = presión absoluta (Pa)
- **R** = constante específica del aire = 287.05 J/(kg·K)
- **T** = temperatura absoluta (K) = °C + 273.15

## Datos de Entrada

El script usa datos JSON con la estructura:
```json
[
  {
    "tiempo_ms": 0,
    "presion": 1019.74,      // en hPa, se convierte a Pa
    "temperatura": 20.64     // en °C
  },
  ...
]
```

**Parámetros requeridos:**
- `tiempo_ms`: Tiempo en milisegundos
- `presion`: Presión en hectopascales (hPa)
- `temperatura`: Temperatura en grados Celsius (°C)

## Características Principales

### 1. Cálculo de Densidad
- Conversión automática de unidades (hPa → Pa, °C → K)
- Aplicación de la ecuación del gas ideal
- Validación de datos

### 2. Estimación de Altitud
- Fórmula barométrica simplificada
- Válida para altitudes < 10 km
- Correlación con densidad

### 3. Gráficas Generadas

#### Gráfica 1: Densidad vs Tiempo
- Muestra la evolución temporal de la densidad
- Identifica máximos y mínimos

#### Gráfica 2: Densidad vs Altitud ⭐ (PRINCIPAL)
- Relación clara densidad-altitud
- Código de colores por tiempo de vuelo
- Línea de tendencia polinómica

#### Gráfica 3: Presión vs Altitud
- Comportamiento barométrico
- Relación exponencial

#### Gráfica 4: Temperatura vs Altitud
- Variación térmica durante el vuelo
- Efecto sobre la densidad

#### Gráfica 5: Número de Reynolds vs Tiempo
- Indicador del régimen de flujo (laminar/turbulento)
- Transición en Re ≈ 10⁵

#### Gráfica 6: Fuerza de Arrastre vs Tiempo
- Fuerza de resistencia aerodinámica
- F_drag = 0.5 × ρ × v² × Cd × A
- Efecto directo de la densidad

## Cómo la Densidad Afecta la Aerodinámica

### 1. **RESISTENCIA AERODINÁMICA (ARRASTRE)**

La resistencia es **proporcional a la densidad**:

$$D = \frac{1}{2} \rho v^2 C_d A$$

**Implicaciones:**
- ↑ Densidad → ↑ Resistencia
- En ascenso (baja altitud, alta ρ): Mayor resistencia → menor altura alcanzada
- En descenso (alta altitud, baja ρ): Menor resistencia → mayor velocidad terminal

**Ejemplo:** 
- A nivel del mar: ρ = 1.225 kg/m³
- A 1000 m: ρ ≈ 1.110 kg/m³
- Reducción: ~10%

### 2. **NÚMERO DE REYNOLDS Y RÉGIMEN DE FLUJO**

$$Re = \frac{\rho v D}{\mu}$$

Donde μ es la viscosidad dinámica (1.81 × 10⁻⁵ Pa·s)

**Transiciones:**
- Re < 10³: Flujo fuertemente laminar (Cd alto)
- 10³ < Re < 10⁵: Flujo de transición
- Re > 10⁵: Flujo turbulento (Cd estable)

**Cambios en Cd:**
- Flujo laminar: Cd ≈ 0.5 (cilindro)
- Flujo turbulento: Cd ≈ 1.0-1.2

**Impacto en el cohete:**
- Baja densidad → Re disminuye → Flujo más laminar → Menos arrastre
- Alta densidad → Re aumenta → Flujo turbulento → Más arrastre

### 3. **FUERZAS LATERALES Y ESTABILIDAD**

Las fuerzas laterales (sustentación, fuerzas de aleta) son proporcionales a ρ:

$$F_{lateral} = \frac{1}{2} \rho v^2 C_l A$$

**En ascenso (alta ρ):**
- Mayor control de las aletas
- Mayor estabilidad pero más resistencia total

**En descenso (baja ρ):**
- Menor control de aletas
- Trayectoria menos estable

### 4. **DESPLIEGUE DEL PARACAÍDAS** 🪂

**Crítico:** El paracaídas REQUIERE densidad suficiente para funcionar.

Fuerza de frenado:
$$F_{freno} = \frac{1}{2} \rho v^2 C_d A_{paracaidas}$$

**Problema:** Si se despliega demasiado alto (ρ muy baja):
- Insuficiente fuerza de frenado
- Velocidad de impacto demasiado alta
- Riesgo de daño en recuperación

**Altitud típica de despliegue:** 500-1000 m
- Densidad mínima necesaria: ~1.0 kg/m³
- Presión mínima: ~89.5 kPa

**En nuestro cohete:**
- Despliegue detectado a t ≈ 397 s
- Densidad: ~1.215 kg/m³ ✓ SUFICIENTE

### 5. **OPTIMIZACIÓN AERODINÁMICA**

Para **maximizar altitud**:

1. **Minimizar resistencia en ascenso:**
   - Forma aerodinámica optimizada (coeficiente ballístico)
   - Superficie lisa para reducir Cd
   - Menos diámetro de fuselaje

2. **Maximizar impulso específico:**
   - Aumentar masa de propelante
   - Optimizar razón de mezcla

3. **Altitud óptima de apogeo:**
   - Suficiente densidad para control
   - Insuficiente para frenar ascenso

Para **descenso seguro**:

1. **Despliegue en altitud correcta:**
   - No demasiado alto (ρ insuficiente)
   - No demasiado bajo (tiempo insuficiente)

2. **Área de paracaídas adecuada:**
   - Función de masa y velocidad en despliegue
   - Considerar variación de ρ

3. **Velocidad terminal:**
   - v_terminal = √(2mg / (ρ × Cd × A))
   - Mayor ρ → Menor v_terminal → Descenso más suave

## Fórmulas Importantes

### Densidad del Aire
```
ρ = P / (R × T)
```

### Altitud Barométrica
```
h = (T₀/Γ) × [(P/P₀)^(-ΓR/g) - 1]
Donde: Γ = -0.0065 K/m (gradiente adiabático seco)
```

### Número de Reynolds
```
Re = (ρ × v × D) / μ
```

### Fuerza de Arrastre
```
D = 0.5 × ρ × v² × Cd × A
```

### Velocidad Terminal
```
v_t = √(2mg / (ρ × Cd × A))
```

## Constantes Utilizadas

| Constante | Símbolo | Valor | Unidad |
|-----------|---------|-------|--------|
| Constante aire | R | 287.05 | J/(kg·K) |
| Aceleración gravedad | g | 9.81 | m/s² |
| Densidad nivel mar | ρ₀ | 1.225 | kg/m³ |
| Presión nivel mar | P₀ | 101325 | Pa |
| Temperatura nivel mar | T₀ | 288.15 | K |
| Gradiente adiabático | Γ | -0.0065 | K/m |
| Viscosidad aire | μ | 1.81e-5 | Pa·s |

## Archivos Generados

| Archivo | Descripción |
|---------|-------------|
| `grafica_densidad_aerodinamica.png` | Gráficas principales (6 subplots) |
| `analisis_densidad_aire.py` | Script principal |

## Uso

```bash
python analisis_densidad_aire.py
```

**Salida esperada:**
1. Imprime estadísticas de densidad y altitud
2. Genera 6 gráficas científicas
3. Explica el efecto aerodinámico detalladamente

## Estadísticas del Cohete de Prueba

```
Densidad media: 1.2157 kg/m³
Densidad máxima: 1.2236 kg/m³ (nivel bajo)
Densidad mínima: 1.1925 kg/m³ (apogeo)

Variación: 0.0311 kg/m³ (~2.5%)

Número de Reynolds: 10³ - 10⁶ (régimen de transición)
```

## Limitaciones

1. **Fórmula barométrica:** Solo válida para h < 10 km
2. **Aire seco:** No considera humedad
3. **Atmosfera estándar:** Supone atmósfera ideal
4. **Viscosidad:** Se asume constante (no varía mucho)

## Mejoras Futuras

- [ ] Incluir efecto de humedad
- [ ] Modelo atmosférico más preciso (función por capas)
- [ ] Simulación de vuelo integrada
- [ ] Análisis de estabilidad de cabeceo
- [ ] Exportación de coeficientes aerodinámicos

## Referencias

- Anderson, J. D. (2011). *Fundamentals of Aerodynamics*
- ICAO. *International Standard Atmosphere*
- NASA. *Earth Atmosphere Model*

---

**Nota:** Este análisis es fundamental para el diseño seguro y eficiente de cohetes experimentales. La densidad del aire es el factor más importante en la aerodinámica después de la forma del fuselaje.
