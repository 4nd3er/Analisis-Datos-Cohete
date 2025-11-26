# Diagrama del Modelo Predictivo

```mermaid
graph TD
    subgraph "1. Recolección de Datos"
        A[Sensor / Lanzamientos] -->|Datos Crudos| B(datalanzamientos.json)
        B --> C{Filtrar Datos}
        C -->|Sin Electrónica| D[Datos Limpios]
        C -->|Con Electrónica| X[Descartar]
    end

    subgraph "2. Procesamiento y Entrenamiento"
        D -->|Extraer Presión PSI| E[Variable X]
        D -->|Extraer Tiempo de Vuelo| F[Variable t]
        F --> G[Fórmula Littlewood<br/>h = 1.225 * t^2]
        G --> H[Variable Y <br/> Apogeo Calculado]

        E --> I[Entrenamiento del Modelo]
        H --> I
        I --> J[Regresión Polinómica<br/>(Grado 2)]
    end

    subgraph "3. Simulación y Predicción"
        K[Usuario] -->|Ingresa PSI| L[Simulador de Consola]
        J --> L
        L -->|Aplica Modelo| M[Predicción de Altura]
        M --> K
    end

    style J fill:#f9f,stroke:#333,stroke-width:4px
    style M fill:#bbf,stroke:#333,stroke-width:2px
```
