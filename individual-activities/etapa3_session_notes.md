# Notas de Sesión — Proyecto Etapa 3: Aprendizaje con PySpark (Dataset Completo)

**Fecha:** 2026-05-19  
**Rama:** `proyectoetapa3`  
**Archivo principal:** `individual-activities/etapa3_aprendizaje.ipynb`

---

## 1. Objetivo de la sesión

Implementar el notebook de Etapa 3 del proyecto TC5057 cubriendo las 5 secciones requeridas:
aprendizaje supervisado y no supervisado sobre la muestra M **completa** (no reducida) de GTEx V10,
con PySpark MLlib, siguiendo la metodología y mejoras acumuladas en Tareas 3 y 4.

---

## 2. Diferencias clave respecto a Tareas 3 y 4

| Aspecto | Tarea 3 / Tarea 4 | Etapa 3 |
|---------|------------------|---------|
| Tamaño de M | 799 muestras (2 grupos) | **19,616 muestras (10 particiones)** |
| Particiones | P05–P08 (cardiovascular + musculoesquelético) | P01–P10 (todos los 5 grupos de tejido) |
| Carga del dataset | Sub-muestra reducida (GENE_STEP=100) | Lectura por bloques (chunksize=500 genes) |
| División | Estratificada aleatoria (Tarea 3 Exp.1-2) / por donante (Tarea 3 Exp.3) | **Por donante (GroupShuffleSplit)** |
| Modelos | RF binario (Tarea 3) + K-Means/GMM (Tarea 4) | RF 5 clases + K-Means (dataset completo) |
| Variable objetivo supervisada | TISSUE_GROUP (2 clases) o SMTSD (11 sub-tipos) | **TISSUE_GROUP (5 clases)** |

---

## 3. Estructura del notebook (32 celdas)

| Sección | Celdas | Contenido |
|---------|--------|-----------|
| 1. Construcción de M | 2–10 | Imports, Spark, metadatos, distribución de particiones, mapeo dash→underscore, cálculo de varianza chunked, top-500 genes, construcción de la matriz M |
| 2. Train-Test | 11–14 | LabelEncoder, GroupShuffleSplit por SUBJID, verificación Tri∩Tsi=∅, estadísticas de distribución |
| 3. Métricas | 15–16 | Discusión de métricas (markdown), definición de evaluadores PySpark + sklearn |
| 4. Entrenamiento | 17–29 | StandardScaler+PCA(50), Spark DFs, RF training, evaluación, confusión, importancia de genes, elbow k=2..7, K-Means k_opt, evaluación clustering |
| 5. Análisis | 30 | Resultados reales por clase, fortalezas, áreas de oportunidad, implicaciones para medicina espacial |
| Referencias | 31 | Breiman 2001, GTEx 2020, Law 2016, scikit-learn, Spark |

---

## 4. Decisiones de diseño

### 4.1 Estrategia de carga del dataset completo

El archivo TPM tiene 59,033 genes × 19,788 muestras ≈ 4.7 GB. Cargarlo completo en memoria
no es factible. Se aplicó una estrategia en dos pasos:

1. **Cálculo de varianza por bloques:** lectura chunked (500 genes/bloque) con `pandas.read_csv`,
   procesando un bloque a la vez (~80 MB pico). 119 bloques × 59,033 genes totales.
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
# Leer con nombres originales del archivo, renombrar inmediatamente después
chunk = chunk.rename(columns=rename_dash_to_san)
```

### 4.3 Preprocesamiento para K-Means

Se usa sklearn (no PySpark MLlib) para StandardScaler + PCA — misma decisión técnica que
Tarea 4, validada para evitar el crash del Python worker en Windows con vectores densos de alta
dimensión. K-Means y RF siguen ejecutándose en PySpark MLlib.

### 4.4 División por donante

`GroupShuffleSplit(test_size=0.20, random_state=42)` agrupando por `SUBJID`.
Con 946 donantes únicos (de 981 totales), el split resultó en:
- Train: 15,620 muestras, 756 donantes
- Test: 3,996 muestras, 190 donantes
- Donantes compartidos: **0** (verificado)

---

## 5. Resultados obtenidos

### 5.1 Muestra M

| Métrica | Valor |
|---------|-------|
| Muestras totales en M | 19,616 |
| Donantes únicos | 946 |
| Genes seleccionados | 500 (por varianza) |
| Particiones cubiertas | 10 (5 grupos × 2 sexos) |
| Tamaño en memoria | 78.5 MB |

Distribución por grupo:

| TISSUE_GROUP | Muestras |
|-------------|----------|
| Visceral_Metabolico | 7,785 |
| Musculoesqueletico | 4,176 |
| Nervioso | 3,904 |
| Cardiovascular | 2,344 |
| Hematopoyetico | 1,407 |

### 5.2 PCA

| Componentes | Varianza acumulada |
|------------|-------------------|
| PC 1–5 | 37.7% |
| PC 1–10 | 53.7% |
| PC 1–20 | 67.5% |
| PC 1–50 | 82.8% |

Nota: con el dataset completo (vs 799 muestras en Tarea 4), la varianza en los primeros 50 PCs
es menor (82.8% vs 90.7%), indicando mayor heterogeneidad en el transcriptoma de 19,616 muestras.

### 5.3 Random Forest (supervisado, 5 clases)

| Clase | Precision | Recall | F1 | Soporte |
|-------|-----------|--------|----|---------|
| Cardiovascular | 1.00 | 0.98 | 0.99 | 473 |
| Hematopoyetico | 1.00 | 1.00 | 1.00 | 284 |
| Musculoesquelético | 0.95 | 0.99 | 0.97 | 865 |
| Nervioso | 1.00 | 1.00 | 1.00 | 808 |
| Visceral_Metabólico | 0.99 | 0.97 | 0.98 | 1,566 |
| **Macro avg** | **0.99** | **0.99** | **0.99** | **3,996** |

**Accuracy: 98.42% · F1-macro: 98.43%**

La clase con más errores es Musculoesquelético (precision=0.95): confusiones con
Visceral_Metabólico por genes metabólicos compartidos entre tejido adiposo y órganos digestivos.

### 5.4 K-Means (no supervisado)

| k | Silhouette | WCSS (train) |
|---|-----------|--------------|
| 2 | 0.1646 | 5,631,143 |
| 3 | 0.1827 | 5,249,681 |
| 4 | 0.2016 | 4,876,595 |
| 5 | 0.1771 | 4,737,735 |
| 6 | 0.2149 | 4,215,261 |
| **7** | **0.2283** ← óptimo | 4,002,651 |

**k_óptimo = 7** (vs k=5 en Tarea 4 con 799 muestras). Con más muestras aparece sub-estructura
dentro de Visceral_Metabólico (hígado, páncreas, órganos digestivos como clusters separados).

**Silhouette = 0.2283 · Pureza = 59.83%**

---

## 6. Problemas técnicos y soluciones

### 6.1 M vacía por mismatch dash vs underscore

**Problema:** `valid_sample_cols` resultaba vacío porque el archivo GTEx usa guiones en
los nombres de columna pero `meta_col_names` (de Spark) usa guiones bajos.

**Error:** `ValueError: Found array with 0 sample(s)` en `GroupShuffleSplit`.

**Solución:** construir un diccionario de mapeo `{nombre_archivo: nombre_sanitizado}` y
renombrar columnas inmediatamente después de leer cada chunk.

### 6.2 Tiempo de procesamiento elevado

La lectura chunked de 119 bloques × 19,616 columnas tomó ~15 minutos. Es el cuello de botella
esperado con un dataset de ~4.7 GB. Documentado en la Sección 1 del notebook como decisión de
ingeniería justificada.

---

## 7. Commits realizados

| Hash | Descripción |
|------|-------------|
| `8cd69f6` | Add Etapa 3 notebook: full-dataset supervised + unsupervised learning |
| (próximo) | Add session notes |

---

## 8. Estado actual

- Notebook ejecutado con todos los outputs guardados (32 celdas)
- Branch pusheado a `origin/proyectoetapa3`
- Sin PR (solicitado explícitamente por el usuario)
