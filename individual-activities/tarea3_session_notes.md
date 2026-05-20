# Notas de Sesión — Tarea 3: Aprendizaje Supervisado con PySpark

**Fecha:** 2026-05-18 (actualizado 2026-05-19)  
**Rama:** `diegofalcon/tarea3-supervised-learning`  
**Archivo principal:** `individual-activities/tarea3_supervised_learning.ipynb`

---

## 1. Objetivo de la sesión

Implementar la Tarea 3 del proyecto TC5057 — construir un pipeline de aprendizaje supervisado con PySpark MLlib sobre el dataset GTEx V10, alineado con la metodología de Etapa 2 (muestreo estratificado, particiones por grupo de tejido y sexo).

---

## 2. Estructura del notebook generado

| Sección | Contenido |
|---------|-----------|
| 1. Introducción | Concepto de aprendizaje supervisado, tabla de 7 algoritmos, tabla de clases MLlib, justificación de Random Forest |
| 2. Selección de datos | Sub-muestra M' (P05–P08), 200 muestras/partición, estratificado por SMTSD |
| 3. Preparación train/test | División estratificada 80/20 con `sklearn.train_test_split` |
| 4. Construcción del modelo | Pipeline MLlib: VectorAssembler + RandomForestClassifier, evaluación AUC/Accuracy/F1, matriz de confusión, importancia de genes |
| 5. Optimización | Selección de features por varianza (top-500 genes de mayor varianza) vs selección aleatoria |
| 6. Experimento 3 | Mejoras derivadas de Tarea 4: target SMTSD (11 sub-tipos) + `GroupShuffleSplit` por donante; Accuracy=0.9613, F1=0.9609 |

---

## 3. Decisiones de diseño

### 3.1 Variable objetivo: TISSUE_GROUP (no SEX_LABEL)

El target original era `SEX_LABEL` (Masculino/Femenino). Se cambió a `TISSUE_GROUP` (Cardiovascular vs Musculoesquelético) por dos razones:

1. **Data leakage con SEX_LABEL:** los genes del cromosoma Y están determinísticamente ausentes en mujeres, haciendo que AUC=1.0 sea circular (el gen Y **es** el sexo, no lo predice).
2. **Alineación con Tarea 2:** el grupo de tejido fue la variable de partición principal en Etapa 2. Predecir TISSUE_GROUP es coherente con el objetivo de medicina espacial — GTEx como línea base de expresión normal para comparar con astronautas.

### 3.2 Sub-muestra M'

- Particiones: P05 (Cardiovascular+Femenino), P06 (Cardiovascular+Masculino), P07 (Musculoesquelético+Femenino), P08 (Musculoesquelético+Masculino)
- 200 muestras por partición, estratificadas proporcionalmente por subtipo de tejido (SMTSD)
- Total: 799 muestras (una partición tuvo 199 disponibles)

### 3.3 Experimentos 1, 2 y 3

| | Experimento 1 | Experimento 2 | Experimento 3 |
|---|---|---|---|
| Selección de genes | 500 aleatorios | 500 de mayor varianza | 500 de mayor varianza |
| Variable objetivo | TISSUE_GROUP (2 clases) | TISSUE_GROUP (2 clases) | SMTSD (11 sub-tipos) |
| División | 80/20 aleatorio | 80/20 aleatorio | 80/20 por donante (`GroupShuffleSplit`) |
| AUC-ROC | 1.0000 | 1.0000 | N/A (multi-clase) |
| Accuracy | 1.0000 | 1.0000 | **0.9613** |
| F1-Score | 1.0000 | 1.0000 | **0.9609** |

**Por qué AUC=1.0 en Exp. 1 y 2 no es data leakage:** cardiovascular vs musculoesquelético es el par de tejidos con mayor divergencia en el genoma (~8–17% de genes diferencialmente expresados). Con 500 genes al azar de 59,033, la probabilidad de capturar al menos un marcador tisular es ~99.99%. Clasificadores RNA-seq de tejido alcanzan >95% de precisión en la literatura — GTEx mismo usa esto para QC de muestras.

**Por qué Exp. 3 es más representativo:** la tarea de SMTSD (11 sub-tipos) es genuinamente difícil — los sub-tipos comparten la mayoría del perfil de expresión. El split por donante elimina el riesgo de aprender perfiles individuales (412 donantes en train, 104 en test, 0 solapamiento).

### 3.4 Genes más importantes (Experimento 2)

Top marcadores identificados por Random Forest:  
**PLN** (phospholamban), **ACTN2** (actinina cardíaca), **MYL7/MYL4** (miosina cardíaca), **ACTC1** (actina cardíaca), **TPM1** (tropomiosina), **MYOZ2** (miozenina), **CNN1** (calponina muscular lisa).

Todos son marcadores conocidos de tejido cardiovascular/muscular — validación biológica del modelo.

---

## 4. Problemas técnicos y soluciones

### 4.1 JAVA_HOME no configurado en el kernel `big-data`

**Problema:** nbconvert lanza el kernel Python del entorno conda `big-data`, que no hereda `JAVA_HOME`. PySpark no puede arrancar.

**Solución:** detectar el entorno conda desde dentro del notebook y setear `JAVA_HOME` antes de importar PySpark:

```python
_conda_env = os.path.dirname(sys.executable)
_java_home = os.path.join(_conda_env, 'Library', 'lib', 'jvm')
if os.path.isdir(_java_home):
    os.environ['JAVA_HOME'] = _java_home
```

También se instaló `openjdk=17` en el entorno:
```
conda install -n big-data -c conda-forge openjdk=17 -y
```

### 4.2 ModuleNotFoundError: sklearn

`scikit-learn` no estaba en el entorno `big-data`. Se instaló y se agregó a `environment.yml`:
```
conda install -n big-data -c conda-forge scikit-learn -y
```

### 4.3 IllegalArgumentException: FIELD_NOT_FOUND en Spark

**Problema:** los IDs de genes GTEx tienen puntos (e.g. `ENSG00000253852.1`). Spark interpreta el punto como acceso a campo anidado (struct), fallando al construir el `VectorAssembler`.

**Solución:** sanitizar los nombres de columna antes de crear el DataFrame Spark:
```python
rename_map = {g: g.replace('.', '_') for g in selected_gene_ids}
tpm_T = tpm_T.rename(columns=rename_map)
gene_cols = [rename_map[g] for g in selected_gene_ids]
```

---

## 5. Correcciones de texto aplicadas durante la sesión

Tras el cambio de target variable (SEX_LABEL → TISSUE_GROUP) quedaron referencias desactualizadas en celdas markdown:

| Celda | Texto incorrecto | Texto corregido |
|-------|-----------------|-----------------|
| `cell-10-traintest-header` | "Masculino / Femenino" | "Cardiovascular / Musculoesquelético" |
| `cell-10-traintest-header` | "concentrar más muestras de un sexo" | "de un tipo de tejido" |
| `cell-20-feat-importance` | `print('... para clasificar el sexo')` | `print('... para clasificar el tipo de tejido')` |

---

## 6. Experimento 3 — Detalle técnico (Sección 6 del notebook)

### 6.1 Origen de las mejoras

Derivadas directamente del análisis no supervisado de Tarea 4:
- **k=5 óptimo en K-Means** → la muestra M' tiene 5+ sub-grupos naturales; clasificar TISSUE_GROUP colapsaba esto en 2 clases triviales.
- **Split aleatorio** → permite leakage inter-donante; el modelo aprende perfiles individuales en lugar de patrones generalizables.

### 6.2 Implementación

```python
# Obtener SMTSD y SUBJID de meta_target
meta_pd = meta_target.select('COL_NAME', 'SMTSD', 'SUBJID').toPandas()
tpm_exp3 = tpm_opt[['COL_NAME'] + gene_cols_v2].merge(meta_pd, on='COL_NAME', how='inner')

# Codificación multi-clase
le_smtsd = LabelEncoder()
tpm_exp3['smtsd_label'] = le_smtsd.fit_transform(tpm_exp3['SMTSD'])

# Split por donante
gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=RANDOM_SEED)
train_idx, test_idx = next(gss.split(X_exp3, y_exp3, groups=tpm_exp3['SUBJID'].values))
```

### 6.3 Resultados

**Sub-tipos identificados (11 clases):**

| Código | SMTSD | Muestras |
|--------|-------|----------|
| 0 | Adipose - Subcutaneous | 69 |
| 1 | Adipose - Visceral (Omentum) | 56 |
| 2 | Artery - Aorta | 82 |
| 3 | Artery - Coronary | 47 |
| 4 | Artery - Tibial | 117 |
| 5 | Cells - Cultured fibroblasts | 63 |
| 6 | Heart - Atrial Appendage | 77 |
| 7 | Heart - Left Ventricle | 76 |
| 8 | Muscle - Skeletal | 78 |
| 9 | Skin - Not Sun Exposed (Suprapubic) | 62 |
| 10 | Skin - Sun Exposed (Lower leg) | 72 |

**Split:** 644 train (412 donantes) / 155 test (104 donantes) — 0 solapamiento confirmado.

**Métricas finales:** Accuracy = 0.9613, F1 macro = 0.9609.

---

## 7. Commits realizados

| Hash | Descripción |
|------|-------------|
| `fc0031c` | Add Tarea 3 supervised learning notebook (initial) |
| `cc45aa9` | Execute notebook and update interpretation with real results |
| `188c3ae` | Add optimization section: variance-based gene selection |
| `78371bb` | Change target variable to TISSUE_GROUP |
| `12d65e5` | Fix stale sex references in markdown and print statements |
| `740f046` | Add Experiment 3: SMTSD multi-class classification with donor-based split |

---

## 8. Estado actual

- Notebook ejecutado con todos los outputs guardados (39 celdas)
- Tres experimentos completos con resultados reales
- Todos los cambios pusheados a `origin/diegofalcon/tarea3-supervised-learning`
- Pendiente: PR hacia `main` con la entrega final
