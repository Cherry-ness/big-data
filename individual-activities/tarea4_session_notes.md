# Notas de Sesión — Tarea 4: Aprendizaje No Supervisado con PySpark

**Fecha:** 2026-05-19  
**Rama:** `diegofalcon/tarea4_unsupervised-learning`  
**Archivo principal:** `individual-activities/tarea4_unsupervised_learning.ipynb`

---

## 1. Objetivo de la sesión

Implementar la Tarea 4 del proyecto TC5057 — construir un pipeline de aprendizaje **no supervisado** con PySpark MLlib (K-Means y GMM) sobre la misma muestra M' de Tarea 3, y comparar los hallazgos con el experimento supervisado previo.

---

## 2. Estructura del notebook generado

| Sección | Contenido |
|---------|-----------|
| 1. Introducción | Concepto de aprendizaje no supervisado, tabla de 8 algoritmos, tabla de clases MLlib (`KMeans`, `BisectingKMeans`, `GaussianMixture`, `LDA`, `PowerIterationClustering`), justificación de K-Means |
| 2. Selección de datos | Misma muestra M' de Tarea 3: 799 muestras (cardiovascular + musculoesquelético), 500 genes por varianza |
| 3. Preparación train/test | División estratificada 80/20; pipeline de preprocesamiento ajustado solo sobre train (no data leakage) |
| 4. Modelos no supervisados | StandardScaler + PCA(50) → K-Means (método del codo k=2..6 + entrenamiento final) + GMM, evaluación con Silhouette y pureza |

---

## 3. Diferencias clave respecto a Tarea 3

| Aspecto | Tarea 3 (Supervisado) | Tarea 4 (No supervisado) |
|---------|----------------------|--------------------------|
| Etiquetas en entrenamiento | Sí (`TISSUE_GROUP`) | No — solo validación externa post-hoc |
| Algoritmo | Random Forest (100 árboles) | K-Means + GMM |
| Preprocesamiento | Solo VectorAssembler (RF insensible a escala) | StandardScaler + PCA(50) (K-Means sensible a escala y dimensionalidad) |
| Pipeline completo | Todo PySpark MLlib | sklearn preprocesamiento + PySpark clustering |
| Métrica principal | AUC-ROC (requiere etiquetas) | Silhouette (intrínseca, sin etiquetas) + pureza como validación externa |
| Selección de k | No aplica | Método del codo (Silhouette para k=2..6) |

---

## 4. Resultados obtenidos

### 4.1 Preprocesamiento PCA

| PCs | Varianza acumulada |
|-----|-------------------|
| PC 1–5 | 62.4% |
| PC 1–10 | 72.3% |
| PC 1–50 | 90.7% |

Los primeros 5 componentes capturan más del 60% de la varianza — fuerte señal de estructura en los datos.

### 4.2 Método del codo

| k | Silhouette | WCSS (train) |
|---|-----------|--------------|
| 2 | 0.1778 | 254,287 |
| 3 | 0.2785 | 176,129 |
| 4 | 0.3129 | 148,689 |
| **5** | **0.3688** ← óptimo | 129,283 |
| 6 | 0.2671 | 125,132 |

**Hallazgo clave:** el k óptimo es **5**, no 2. Esto revela que existen **5 sub-clusters naturales** en los datos, correspondientes a sub-tipos de tejido (`SMTSD`) dentro de cada grupo (piel ≠ músculo; corazón ≠ vasos sanguíneos).

### 4.3 K-Means k=2

| Métrica | Valor |
|---------|-------|
| Silhouette | 0.1778 (estructura débil) |
| Pureza | 84.4% (135/160 muestras) |
| WCSS train | 254,287 |

**Tabla de contingencia (test set):**

| Cluster | Cardiovascular | Musculoesquelético | Total |
|---------|---------------|---------------------|-------|
| 0 | 0 | 55 | 55 |
| 1 | 80 | 25 | 105 |

- **Cluster 0**: 100% musculoesquelético — probablemente piel/tejido adiposo (perfiles muy distintos a cardiovascular).
- **Cluster 1**: 76% cardiovascular, 24% musculoesquelético — tejidos de borde (músculo con alta expresión mitocondrial similar al cardíaco).

### 4.4 GMM k=2

GMM convergió a solución **degenerada** — todas las 160 muestras de prueba asignadas al cluster 0. Causas probables:
1. Convergencia a óptimo local del algoritmo EM.
2. Las últimas componentes PCA (PC30–50) tienen varianza casi cero, desestabilizando la estimación de covarianza gaussiana.
3. Ratio muestras/dimensiones desfavorable para estimación de matrices de covarianza.

---

## 5. Problemas técnicos y soluciones

### 5.1 PySpark `ClusteringEvaluator` falla en Windows

**Problema:** `ClusteringEvaluator` con `distanceMeasure='squaredEuclidean'` lanza `AssertionError: Number of clusters must be greater than one` incluso cuando K-Means produce 2 clusters.

**Diagnóstico:** El evaluador re-ejecuta el plan Spark de forma lazy y en la segunda ejecución obtiene resultados distintos (posible problema de no-determinismo en la materialización lazy sobre Windows).

**Solución:** Reemplazar `ClusteringEvaluator` por `sklearn.metrics.silhouette_score` aplicado post-hoc sobre las predicciones recopiladas con `toPandas()`.

### 5.2 Python worker crash en PySpark pipeline StandardScaler+PCA

**Problema:** Al intentar usar el pipeline `VectorAssembler → StandardScaler → PCA → KMeans` íntegramente en PySpark, el Python worker crashea durante `KMeans.fit()` con `java.io.IOException: An established connection was aborted`.

**Diagnóstico:** Problema conocido de PySpark en Windows con `withMean=True` en `StandardScaler` sobre vectores densos de alta dimensión. El worker process es terminado por Windows durante la ejecución paralela.

**Solución:** Mover el preprocesamiento (StandardScaler + PCA) a **scikit-learn** (opera sobre pandas en memoria del driver), luego convertir a Spark DF con `VectorAssembler` para el clustering. K-Means y GMM siguen ejecutándose en PySpark MLlib.

### 5.3 VectorUDT vs ArrayType en DataFrames Spark

**Problema inicial:** Al crear DataFrames Spark con `Vectors.dense()` sin schema explícito, `spark.createDataFrame()` infería `ArrayType(DoubleType)` en lugar de `VectorUDT`. K-Means aceptaba el tipo pero producía clustering degenerado.

**Solución:** Usar `VectorAssembler` (que siempre produce `VectorUDT`) en lugar de crear vectores manuales con schema explícito.

---

## 6. Hallazgos con implicaciones para Tarea 3

El análisis no supervisado revela dos problemas estructurales en Tarea 3 que explican el accuracy de 100%:

### 6.1 Tarea demasiado fácil

El k óptimo de **k=5** (no k=2) indica que los datos tienen 5 sub-grupos naturales. Clasificar `TISSUE_GROUP` (cardiovascular vs musculoesquelético) colapsa estos 5 sub-grupos en 2 clases muy separadas — equivale a clasificar "animal vs vegetal" en lugar de "especie por especie".

**Reforma propuesta:** usar `SMTSD` como variable objetivo (~10 sub-tipos de tejido). Problema genuinamente difícil donde RF no obtendrá 100%.

### 6.2 Split sin control de donante

La división 80/20 por muestra permite que muestras del mismo donante aparezcan en train y test. Con ~400 donantes y 800 muestras, ~20% de los donantes contribuyen múltiples muestras. El modelo puede aprender perfiles individuales en lugar de patrones generalizables.

**Reforma propuesta:** `GroupShuffleSplit` por `SUBJID` (donante) — garantiza que ningún donante aparece en ambos conjuntos. Evaluación más honesta de la generalización.

---

## 7. Commits realizados

| Hash | Descripción |
|------|-------------|
| `cb2a1b1` | Add Tarea 4 unsupervised learning notebook |
| `9d9bea5` | Execute notebook and update interpretation with real results |

---

## 8. Estado actual

- Notebook ejecutado con todos los outputs guardados
- Branch pusheado a `origin/diegofalcon/tarea4_unsupervised-learning`
- Pendiente: implementar reformas en Tarea 3 (Sección 6 del notebook de tarea3)
