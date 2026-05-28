# Notas de Sesión — Proyecto Etapa 3: Aprendizaje con PySpark (Dataset Completo)

**Fecha inicial:** 2026-05-19  
**Última actualización:** 2026-05-27  
**Rama:** `proyectoetapa3`  
**Archivo principal:** `individual-activities/etapa3_aprendizaje.ipynb`

---

## 1. Objetivo de la sesión

Implementar el notebook de Etapa 3 del proyecto TC5057 cubriendo las 5 secciones requeridas:
aprendizaje supervisado y no supervisado sobre la muestra M **completa** (no reducida) de GTEx V10,
con PySpark MLlib, siguiendo la metodología y mejoras acumuladas en Tareas 3 y 4.

---

## 2. Diferencias clave respecto a Tareas 3 y 4

| Aspecto | Tarea 3 / Tarea 4 | Etapa 3 (versión actual) |
|---------|------------------|---------|
| Tamaño de M | 799 muestras (2 grupos) | **19,616 muestras (10 particiones)** |
| Particiones | P05–P08 (cardiovascular + musculoesquelético) | P01–P10 (todos los 5 grupos de tejido) |
| Carga del dataset | Sub-muestra reducida (GENE_STEP=100) | Lectura por bloques (chunksize=500 genes) |
| División | Estratificada aleatoria / por donante | **Por donante (GroupShuffleSplit)** |
| Variable objetivo supervisada | TISSUE_GROUP (2–5 clases) | **SMTSD (54 sub-tipos de tejido)** |
| RF implementation | PySpark MLlib | **sklearn** (ver sección 4.4) |
| K-Means implementation | PySpark MLlib | **PySpark MLlib** |

---

## 3. Estructura del notebook (32 celdas)

| Sección | Celdas | Contenido |
|---------|--------|-----------|
| 1. Construcción de M | 2–10 | Imports, Spark, metadatos, distribución de particiones, mapeo dash→underscore, cálculo de varianza chunked, top-500 genes, construcción de la matriz M |
| 2. Train-Test | 11–14 | LabelEncoder (SMTSD), GroupShuffleSplit por SUBJID, verificación Tri∩Tsi=∅, estadísticas de distribución por sub-tipo |
| 3. Métricas | 15–16 | Discusión de métricas (markdown), definición de evaluadores sklearn + silhouette |
| 4. Entrenamiento | 17–29 | StandardScaler+PCA(50), Spark DFs para K-Means, RF sklearn, evaluación, top confusiones, importancia de PCs, elbow k=2..7, K-Means k_opt, evaluación clustering |
| 5. Análisis | 30 | Fortalezas, áreas de oportunidad, síntesis medicina espacial |
| Referencias | 31 | Breiman 2001, GTEx 2020, Law 2016, scikit-learn, Spark |

---

## 4. Decisiones de diseño

### 4.1 Estrategia de carga del dataset completo

El archivo TPM tiene 59,033 genes × 19,788 muestras ≈ 4.7 GB. Cargarlo completo en memoria
no es factible. Se aplicó una estrategia en dos pasos:

1. **Cálculo de varianza por bloques:** lectura chunked (500 genes/bloque) con `pandas.read_csv`,
   procesando un bloque a la vez (~80 MB pico). 119 bloques × 59,033 genes totales.
   Varianza calculada de forma vectorizada con `chunk.var(axis=1).to_dict()` (no iterrows).
2. **Carga de la matriz final:** solo las 500 filas de los top genes, para todas las 19,616
   muestras → 78.5 MB en memoria.

### 4.2 Mapeo dash→underscore (bug corregido)

El archivo GTEx usa guiones en los IDs de muestra (`GTEX-1117F-0005-SM-HL9SH`) pero Spark
sanitiza a guiones bajos (`GTEX_1117F_0005_SM_HL9SH`) en `COL_NAME`. Esto causaba que el
filtro `c in meta_col_names` fallara, produciendo `valid_sample_cols = []` y M vacía.

**Solución:**
```python
file_to_san = {c: c.replace('-', '_').replace('.', '_')
               for c in all_file_cols if c not in ('Name', 'Description')}
valid_sample_cols_file = [c for c, san in file_to_san.items() if san in meta_col_names]
rename_dash_to_san     = {c: file_to_san[c] for c in valid_sample_cols_file}
chunk = chunk.rename(columns=rename_dash_to_san)
```

### 4.3 Preprocesamiento: sklearn en driver

Se usa sklearn (no PySpark MLlib) para `StandardScaler` + `PCA(50)` — misma decisión técnica
que Tarea 4, validada para evitar el crash del Python worker en Windows con vectores densos
de alta dimensión.

### 4.4 RF supervisado: sklearn en driver (no PySpark MLlib)

**Razón:** la variable objetivo es `SMTSD` con **54 sub-tipos** de tejido. Con 54 clases,
el `DTStatsAggregator` interno de PySpark MLlib requiere `numClasses × numBins × numFeatures`
por partición. Con 32 workers en modo `local[*]` y el modelo creciendo árbol a árbol como tarea
broadcasted (llegó a 5.8 MiB/tarea), la JVM lanza `OutOfMemoryError: Java heap space`
incluso con `spark.driver.memory = 8g` y features reducidas a 50 PCs.

**Solución:** `sklearn.ensemble.RandomForestClassifier` en el driver:
```python
rf_sk = SklearnRF(n_estimators=100, max_depth=10,
                  max_features='sqrt', random_state=42, n_jobs=-1)
rf_sk.fit(X_train_pca, y_train)
```

**División de responsabilidades resultante:**

| Tarea | Librería |
|-------|---------|
| Carga y joins de metadatos | PySpark SQL |
| StandardScaler + PCA | sklearn (driver) |
| Random Forest (supervisado) | sklearn (driver) |
| K-Means (no supervisado) | PySpark MLlib |
| Silhouette post-hoc | sklearn (driver) |

### 4.5 División por donante

`GroupShuffleSplit(test_size=0.20, random_state=42)` agrupando por `SUBJID`.
Con 946 donantes únicos (de 981 totales), el split resultó en:
- Train: 15,620 muestras, 756 donantes
- Test: 3,996 muestras, 190 donantes
- Donantes compartidos: **0** (verificado)

### 4.6 Variable objetivo: SMTSD en lugar de TISSUE_GROUP

**Motivo del cambio (2026-05-27):** con `TISSUE_GROUP` (5 clases macro), RF alcanzó 98.42%
de accuracy. Esa cifra, aunque legítima biológicamente, refleja que los 5 grupos son tan
distintos que cualquier clasificador los separa. El modelo no demuestra aprendizaje de
patrones sutiles.

Con `SMTSD` (54 sub-tipos), el modelo debe distinguir sub-tejidos biológicamente cercanos
(regiones cerebrales, tipos de arteria, secciones de colon, etc.) — un problema genuinamente
difícil que produce un accuracy más honesto y un modelo más útil para detección de anomalías
en medicina espacial.

---

## 5. Resultados obtenidos

### 5.1 Muestra M

| Métrica | Valor |
|---------|-------|
| Muestras totales en M | 19,616 |
| Donantes únicos | 946 |
| Genes seleccionados | 500 (por varianza) |
| Sub-tipos SMTSD | 54 |
| Tamaño en memoria | 78.5 MB |

### 5.2 PCA

| Componentes | Varianza acumulada |
|------------|-------------------|
| PC 1–5 | 37.7% |
| PC 1–10 | 53.7% |
| PC 1–20 | 67.5% |
| PC 1–50 | 82.8% |

### 5.3 Random Forest (supervisado, SMTSD — 54 clases)

**Pendiente de ejecución** — notebook no re-ejecutado al cierre de esta sesión.
La ejecución anterior con TISSUE_GROUP (5 clases) dio: Accuracy=98.42%, F1-macro=98.43%.
Con SMTSD se espera accuracy en rango 75–90%.

### 5.4 K-Means (no supervisado) — resultados con TISSUE_GROUP como referencia

| k | Silhouette | WCSS (train) |
|---|-----------|--------------|
| 2 | 0.1646 | 5,631,143 |
| 3 | 0.1827 | 5,249,681 |
| 4 | 0.2016 | 4,876,595 |
| 5 | 0.1771 | 4,737,735 |
| 6 | 0.2149 | 4,215,261 |
| **7** | **0.2283** ← óptimo | 4,002,651 |

**k_óptimo = 7 · Silhouette = 0.2283 · Pureza = 59.83%**

Nota: pureza calculada con etiquetas TISSUE_GROUP como referencia. Con SMTSD como etiqueta
de referencia la pureza será distinta (pendiente).

---

## 6. Problemas técnicos y soluciones

### 6.1 M vacía por mismatch dash vs underscore

**Error:** `ValueError: Found array with 0 sample(s)` en `GroupShuffleSplit`.  
**Solución:** diccionario de mapeo `{nombre_archivo: nombre_sanitizado}` + rename inmediato. (ver §4.2)

### 6.2 OOM en PySpark RF con 54 clases SMTSD

**Error:** `java.lang.OutOfMemoryError: Java heap space` en `DTStatsAggregator`.  
**Intentos fallidos:** (1) usar PCA features (50 dims) en lugar de 500 genes crudos — OOM persiste porque el cuello de botella es `numClasses`, no `numFeatures`. (2) la tarea broadcasted creció hasta 5.8 MiB con 54 clases.  
**Solución:** migrar RF a sklearn en el driver. (ver §4.4)

### 6.3 Tiempo de procesamiento elevado

La lectura chunked de 119 bloques × 19,616 columnas tomó ~15 minutos. Cuello de botella
esperado con un dataset de ~4.7 GB.

---

## 7. Commits realizados

| Hash | Descripción |
|------|-------------|
| `8cd69f6` | Add Etapa 3 notebook: full-dataset supervised + unsupervised learning |
| `762c18f` | Optimize etapa3 notebook: rubric compliance, vectorized variance, gene symbols |

---

## 8. Estado actual (2026-05-27)

- Notebook modificado con variable objetivo **SMTSD** (54 clases) y RF en sklearn
- **Notebook NO re-ejecutado** — cambios aplicados al código pero outputs aún del run anterior (TISSUE_GROUP)
- Cambios no commiteados ni pusheados (pendiente para próxima sesión)
- K-Means sin cambios — sigue en PySpark MLlib
