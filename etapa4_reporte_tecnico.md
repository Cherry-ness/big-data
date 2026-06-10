# Detección de Patrones de Expresión Génica en Tejido Nervioso Humano mediante Aprendizaje Automático sobre Grandes Volúmenes de Datos

**Autor:** Diego Falcón Costilla · A01139580  
**Curso:** TC5057 — Análisis de Grandes Volúmenes de Datos  
**Institución:** Tecnológico de Monterrey  
**Profesor:** Dr. Iván Olmos Pineda  
**Tutor:** José Carlos Soto · Equipo #17  
**Fecha:** Junio 2026

---

> **Video explicativo:** [Enlace al video — YouTube/Drive] *(subir antes de la entrega final)*

---

## Resumen

Este proyecto aplica técnicas de aprendizaje automático supervisado y no supervisado sobre el dataset GTEx Analysis V10 (NIH/Broad Institute), que contiene perfiles de expresión génica en unidades TPM de 59,033 genes medidos en 19,788 muestras de 981 donantes adultos. El objetivo es construir un modelo capaz de identificar la región cerebral de origen de una muestra biológica a partir de su firma transcriptómica, estableciendo una línea base molecular del transcriptoma cerebral humano sano. Se seleccionan los 500 genes de mayor varianza inter-muestras y se aplica PCA(50 componentes) como preprocesamiento. El modelo de Random Forest (PySpark MLlib) clasificó 14 sub-tipos de tejido nervioso (SMTSD) con Accuracy 0.7723 ± 0.014 y F1-macro 0.7698 ± 0.016 en validación cruzada de 5 pliegues por donante, confirmando que los patrones moleculares por región cerebral son reproducibles entre individuos distintos. El análisis no supervisado con K-Means obtuvo Silhouette 0.6022, revelando dos macro-agrupaciones biológicamente coherentes.

---

## 1. Introducción

### 1.1 Antecedentes

El proyecto GTEx (Genotype-Tissue Expression) es una iniciativa del NIH que cataloga la variación en expresión génica entre individuos y tejidos usando datos de RNA-seq de más de 900 donantes humanos adultos. La versión 10 (GTEx V10), publicada en 2022, es el atlas de expresión génica en tejido humano más completo disponible públicamente, con 19,788 muestras RNASEQ que cubren 54 tipos de tejido.

En paralelo, la creciente actividad en exploración espacial humana plantea preguntas científicas urgentes sobre el efecto de la microgravedad y la radiación cósmica sobre la fisiología humana. Estudios como el NASA Twin Study (Scott Kelly, 2019) demostraron alteraciones en la metilación del ADN, expresión génica y estructura telomérica en astronautas tras vuelos de larga duración. Sin embargo, la línea base del transcriptoma cerebral humano normal —contra la cual comparar estas alteraciones— no está suficientemente establecida en términos cuantitativos de machine learning.

### 1.2 Problema de investigación

El problema central de este proyecto es: **¿Puede un modelo de aprendizaje automático entrenado sobre datos GTEx identificar de forma confiable la región cerebral de origen de una muestra de tejido nervioso a partir de su perfil de expresión génica, generalizando a individuos no vistos en entrenamiento?**

Si la respuesta es afirmativa, el modelo constituye una línea base molecular que permitiría detectar desviaciones en el transcriptoma de astronautas — posibles indicadores de daño neurológico inducido por vuelo espacial.

### 1.3 Objetivos

**Objetivo general:** Construir modelos de aprendizaje supervisado y no supervisado que identifiquen patrones de expresión génica en tejido nervioso humano, generalizables a individuos no presentes en el entrenamiento.

**Objetivos específicos:**
1. Caracterizar la población GTEx V10 y construir una muestra M representativa de la diversidad tisular.
2. Seleccionar features biológicamente relevantes (genes de alta varianza) y reducir la dimensionalidad mediante PCA.
3. Entrenar un Random Forest en PySpark MLlib para clasificar 14 sub-tipos de tejido nervioso (SMTSD).
4. Validar la robustez del modelo mediante validación cruzada de 5 pliegues con división por donante.
5. Analizar la estructura natural del espacio de expresión génica con K-Means.
6. Visualizar e interpretar los resultados en términos biológicamente significativos.

### 1.4 Justificación

La clasificación de regiones cerebrales por perfil transcriptómico es un problema de alta dimensionalidad (59,033 genes), desbalanceado (regiones con 670 muestras vs. 181), y biológicamente exigente — regiones anatómicamente adyacentes como caudado y putamen comparten la mayoría de su transcriptoma. Resolverlo satisfactoriamente con un clasificador que generaliza entre donantes es evidencia de que las firmas moleculares cerebrales son más un producto del tipo celular que de la identidad individual — condición necesaria para su uso en medicina espacial.

---

## 2. Propuesta de solución

### 2.1 Descripción general

La propuesta integra cuatro etapas: (1) construcción de la muestra M a partir de las variables de caracterización de la población GTEx, (2) ingeniería de features basada en varianza y PCA, (3) entrenamiento de un Random Forest distribuido en PySpark con validación cruzada por donante, y (4) análisis complementario con K-Means para verificar si las regiones cerebrales forman clusters naturales sin supervisión.

```
Dataset GTEx V10 (59k genes × 19.8k muestras)
         │
         ▼
  Metadatos SMTS/SMTSD + SEX + SUBJID
         │
         ▼
  Muestra M: 10 particiones (TISSUE_GROUP × SEX_LABEL)
         │
         ▼
  M_nervioso: 3,904 muestras · 786 donantes · 14 clases
         │
         ▼
  Top-500 genes por varianza → StandardScaler → PCA(50)
         │
    ┌────┴────┐
    ▼         ▼
 RF 5-fold   K-Means
 GroupKFold  (k=2)
    │         │
 Acc 0.77   Sil 0.60
```

### 2.2 Caracterización de la población

**Población objetivo (P):** donantes adultos del proyecto GTEx V10 con datos RNASEQ disponibles.

| Variable | Descripción | Valores |
|----------|-------------|---------|
| `SMTS` | Tipo de tejido mayor (24 tipos) | Brain, Heart, Muscle, ... |
| `SMTSD` | Sub-tipo de tejido (54 sub-tipos) | Brain - Amygdala, Heart - Left Ventricle, ... |
| `SEX` | Sexo biológico | 1 = Masculino, 2 = Femenino |
| `SUBJID` | Identificador del donante | GTEX-XXXX |
| `SMAFRZE` | Tipo de análisis | RNASEQ (filtro aplicado) |

**Estadísticas de la población:**

| Métrica | Valor |
|---------|-------|
| Muestras RNASEQ totales | 19,788 |
| Donantes únicos | 946 |
| Genes medidos | 59,033 |
| Sub-tipos de tejido | 54 |
| Tamaño del archivo TPM | ~4.7 GB |

### 2.3 Recolección de datos

Los datos se obtienen del GTEx Portal (https://gtexportal.org):

| Archivo | Descripción | Tamaño |
|---------|-------------|--------|
| `GTEx_Analysis_2022-06-06_v10_RNASeQCv2.4.2_gene_tpm_non_lcm.gct` | Matriz TPM: 59,033 genes × 19,788 muestras | ~4.7 GB |
| `GTEx_Analysis_v10_Annotations_SampleAttributesDS.txt` | Metadatos de muestras (SMTS, SMTSD, SMAFRZE) | ~3 MB |
| `GTEx_Analysis_v10_Annotations_SubjectPhenotypesDS.txt` | Fenotipos de donantes (SEX, AGE) | ~50 KB |

### 2.4 Construcción de la muestra M

La muestra M se define como el conjunto de **todas las muestras RNASEQ** organizadas en 10 particiones derivadas de las variables de caracterización:

$$M = \{M_i : M_i = \text{TISSUE\_GROUP}_j \times \text{SEX\_LABEL}_k\}, \quad i = 1, \ldots, 10$$

**Agrupación de tejidos en 5 grupos:**

| TISSUE_GROUP | SMTS incluidos | Muestras |
|--------------|----------------|----------|
| Nervioso | Brain, Nerve | 3,904 |
| Visceral_Metabolico | todos los demás | 7,957 |
| Musculoesqueletico | Muscle, Adipose Tissue, Skin | 4,176 |
| Cardiovascular | Heart, Blood Vessel | 2,344 |
| Hematopoyetico | Blood, Bone Marrow, Spleen | 1,407 |

**Distribución de las 10 particiones:**

| Partición | TISSUE_GROUP | SEX_LABEL | N |
|-----------|--------------|-----------|---|
| M₁ | Cardiovascular | Femenino | 771 |
| M₂ | Cardiovascular | Masculino | 1,573 |
| M₃ | Hematopoyetico | Femenino | 475 |
| M₄ | Hematopoyetico | Masculino | 932 |
| M₅ | Musculoesqueletico | Femenino | 1,349 |
| M₆ | Musculoesqueletico | Masculino | 2,827 |
| M₇ | Nervioso | Femenino | 1,066 |
| M₈ | Nervioso | Masculino | 2,838 |
| M₉ | Visceral_Metabolico | Femenino | 2,864 |
| M₁₀ | Visceral_Metabolico | Masculino | 5,093 |

**Subconjunto de trabajo — M_nervioso:** Para la tarea de clasificación de regiones cerebrales se trabaja con las 3,904 muestras del grupo Nervioso, que incluyen 13 regiones cerebrales + nervio tibial (14 clases SMTSD).

### 2.5 Estrategia de muestreo

**Selección de features por varianza (top-500 genes):**

El archivo TPM tiene 59,033 filas (genes). Cargar la matriz completa requiere ~4.7 GB. Se aplica una estrategia de dos pasos:

1. **Cálculo de varianza por bloques:** lectura chunked (500 genes/bloque) con pandas, ~80 MB pico por bloque. Varianza calculada de forma vectorizada: `DataFrame.var(axis=1)`.
2. **Carga de la matriz final:** solo las 500 filas de los top genes → ~78.5 MB en memoria.

La selección por varianza está validada en la literatura de RNA-seq (Law et al., 2016): los genes con mayor varianza inter-muestras son los más discriminantes biológicamente.

**Justificación del tamaño de muestra:** M_nervioso con 3,904 muestras y 786 donantes cubre:
- Las 14 clases SMTSD con balance razonable (181–670 muestras/clase)
- Suficiente diversidad de donantes para validación cruzada por individuo
- Carga computacional manejable en PySpark local

### 2.6 Preparación de conjuntos de entrenamiento y prueba

**División por donante (GroupShuffleSplit / GroupKFold):**

Un mismo donante contribuye muestras de múltiples regiones cerebrales. Si la división es por muestra, muestras del mismo donante aparecen en train y test simultáneamente, permitiendo que el modelo memorice perfiles individuales. Se divide por `SUBJID`:

$$T_{r_j} \cap T_{s_j} = \emptyset \quad \text{a nivel de donante}$$

**Para Etapa 3 (evaluación inicial):** `GroupShuffleSplit(test_size=0.20)` → 3,103 train / 801 test, 0 donantes en común.

**Para validación cruzada:** `GroupKFold(n_splits=5)` → 5 pliegues, cada fold con ~628 donantes en train y ~158 en test.

### 2.7 Selección de métricas

| Métrica | Fórmula | Justificación |
|---------|---------|---------------|
| **Accuracy** | VP+VN / total | Referencia global |
| **F1-macro** | Promedio no ponderado F1 por clase | Penaliza errores en clases raras igual que en frecuentes |
| **Precision y Recall por clase** | TP/(TP+FP), TP/(TP+FN) | Diagnóstico biológico de confusiones entre regiones |
| **Matriz de confusión** | N×N tabla de conteos | Identifica pares de regiones con firmas similares |
| **Silhouette** (no supervisado) | Cohesión vs separación | Calidad geométrica del clustering sin etiquetas |

### 2.8 Selección de algoritmos

#### Aprendizaje supervisado — Random Forest

Se elige Random Forest por:
1. **Alta dimensionalidad:** selección aleatoria de features por árbol reduce varianza sin preprocesamiento manual de genes.
2. **Robustez al sobreajuste:** el promedio de árboles decorrelacionados mitiga la memorización de perfiles individuales.
3. **Importancia de variables:** produce ranking de PCs más discriminantes, interpretable biológicamente.
4. **Disponibilidad en PySpark MLlib:** implementación distribuida nativa, escala a los 19,788 registros GTEx.

#### Aprendizaje no supervisado — K-Means

Se elige K-Means por su interpretabilidad y disponibilidad en PySpark MLlib. Permite verificar si las regiones cerebrales forman agrupaciones naturales sin etiquetas, complementando al clasificador supervisado.

### 2.9 Preprocesamiento y ajuste de hiperparámetros

**Pipeline de preprocesamiento:**
1. `StandardScaler` (sklearn): normaliza a media=0, std=1 — necesario para PCA y K-Means.
2. `PCA(n_components=50)` (sklearn): reduce 500 → 50 features, capturando 87.0% de la varianza. Acelera entrenamiento RF y reduce ruido.

**Hiperparámetros Random Forest (fijos, justificados):**

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| `numTrees` | 100 | Balance estabilidad/tiempo; convergencia empírica |
| `maxDepth` | 10 | Limita sobreajuste; suficiente para 14 clases en PCA(50) |
| `featureSubsetStrategy` | `sqrt` | Estándar clasificación: √50 ≈ 7 PCs/árbol |
| `seed` | 42 | Reproducibilidad |

**Selección de K para K-Means:** método del codo con Silhouette para k=2..12. El k óptimo (mayor Silhouette) resultó k=2.

---

## 3. Experimentación

### 3.1 Configuración experimental

- **Plataforma:** PySpark 4.1.1 en modo local (`local[*]`), 32 workers, 8 GB driver memory
- **Sistema:** Windows 11 Pro, 32 cores, 64 GB RAM
- **Semilla aleatoria:** 42 en todos los experimentos

### 3.2 Varianza explicada por PCA

| PCs | Varianza acumulada |
|-----|-------------------|
| PC1–5 | 48.7% |
| PC1–10 | 61.2% |
| PC1–20 | 73.1% |
| **PC1–50** | **87.0%** |

Los 50 componentes capturan el 87% de la varianza genómica del subconjunto Nervioso, eliminando el ruido de los 450 genes restantes de menor varianza.

### 3.3 Modelo supervisado — Random Forest (Etapa 3, split único)

**Configuración:** GroupShuffleSplit 80/20 por donante. Train: 3,103 muestras (628 donantes). Test: 801 muestras (158 donantes). Solapamiento = 0.

| Métrica | Valor |
|---------|-------|
| **Accuracy** | **0.7740** |
| **F1-macro** | **0.7692** |

**Resultados por sub-tipo (test set):**

| Sub-tipo SMTSD | Precision | Recall | F1 | Support |
|----------------|-----------|--------|----|---------|
| Brain - Amygdala | 0.74 | 0.61 | 0.67 | 41 |
| Brain - Anterior cingulate cortex (BA24) | 0.63 | 0.80 | 0.71 | 45 |
| Brain - Caudate (basal ganglia) | 0.63 | 0.68 | 0.66 | 63 |
| Brain - Cerebellar Hemisphere | 0.77 | 0.88 | 0.82 | 57 |
| Brain - Cerebellum | 0.88 | 0.73 | 0.80 | 60 |
| Brain - Cortex | 0.81 | 0.79 | 0.80 | 53 |
| Brain - Frontal Cortex (BA9) | 0.76 | 0.58 | 0.66 | 53 |
| Brain - Hippocampus | 0.56 | 0.81 | 0.66 | 52 |
| Brain - Hypothalamus | 0.88 | 0.79 | 0.83 | 57 |
| Brain - Nucleus accumbens (basal ganglia) | 0.82 | 0.77 | 0.79 | 60 |
| Brain - Putamen (basal ganglia) | 0.63 | 0.34 | 0.44 | 50 |
| Brain - Spinal cord (cervical c-1) | 0.83 | 0.97 | 0.90 | 36 |
| Brain - Substantia nigra | 0.74 | 0.76 | 0.75 | 42 |
| Nerve - Tibial | 0.94 | 1.00 | 0.97 | 132 |
| **Macro avg** | **0.76** | **0.75** | **0.75** | 801 |

**Confusiones más frecuentes:**

| Real | Predicho | N |
|------|----------|---|
| Putamen (basal ganglia) | Caudate (basal ganglia) | 20 |
| Cerebellum | Cerebellar Hemisphere | 14 |
| Amygdala | Hippocampus | 12 |
| Frontal Cortex (BA9) | Cortex | 10 |

Las confusiones son biológicamente interpretables: caudado y putamen son ambos ganglios basales con alta similitud transcriptómica; cerebelo y hemisferio cerebeloso son estructuras anatómicamente contiguas.

### 3.4 Validación cruzada 5-fold (Actividad 5)

**Configuración:** GroupKFold(n_splits=5) por donante. K=5 justificado por:
- R1: clase más pequeña (Amygdala, 181 muestras) → ≥36 muestras/fold en test (umbral: 30)
- R3: costo computacional lineal en K; minimizar K en contexto Big Data
- R4: equilibrio sesgo-varianza (80% train por fold)

**Resultados por fold:**

| Fold | Train N | Test N | Accuracy | F1-macro |
|------|---------|--------|----------|----------|
| 1 | 3,133 | 771 | 0.7570 | 0.7530 |
| 2 | 3,133 | 771 | 0.7610 | 0.7590 |
| 3 | 3,124 | 780 | 0.7700 | 0.7640 |
| 4 | 3,124 | 780 | 0.7810 | 0.7800 |
| 5 | 3,120 | 784 | 0.7940 | 0.7930 |
| **Media** | — | — | **0.7723** | **0.7698** |
| **Std** | — | — | **0.0144** | **0.0163** |

**Análisis de sobreajuste:**

| Fold | Accuracy Train | Accuracy Test | Brecha |
|------|---------------|---------------|--------|
| 1 | 0.937 | 0.757 | 0.180 |
| 2 | 0.934 | 0.761 | 0.173 |
| 3 | 0.939 | 0.770 | 0.169 |
| 4 | 0.939 | 0.781 | 0.158 |
| 5 | 0.942 | 0.794 | 0.148 |

La brecha train-test (~17 pp) es consistente entre folds (no crece), indicando sobreajuste moderado estructural del RF con `maxDepth=10`, no una fuga de datos.

**Importancia de componentes PCA (top-5, consistentes entre folds):**

| Rank | PC | Importancia media | Std |
|------|----|-------------------|-----|
| 1 | pc00 | 0.119 | 0.004 |
| 2 | pc17 | 0.056 | 0.003 |
| 3 | pc09 | 0.052 | 0.003 |
| 4 | pc06 | 0.047 | 0.002 |
| 5 | pc04 | 0.043 | 0.002 |

### 3.5 Modelo no supervisado — K-Means

**Método del codo (Silhouette para k=2..12):**

| k | Silhouette | WCSS (train) |
|---|------------|--------------|
| **2** | **0.6022** | 890,040 |
| 3 | 0.6022 | 863,430 |
| 4 | 0.2961 | 826,039 |
| 5 | 0.2322 | 783,953 |
| ... | ... | ... |

El k óptimo es **k=2**, con Silhouette 0.6022. Esto refleja la gran separación biológica entre tejido cerebeloso (firmas de células de Purkinje, genes CBLN1, GRID2) y el resto de regiones cerebrales + nervio periférico.

**Evaluación del clustering:**

| Métrica | Valor |
|---------|-------|
| Silhouette (k=2, test) | 0.6022 |
| Pureza | 0.2434 |

La pureza baja (0.24) con k=2 es esperable: con solo 2 clusters para 14 clases, la mayoría de regiones cerebrales caen en el mismo cluster. La alta Silhouette indica separación geométrica clara en el espacio PCA(50), no confusión del modelo.

### 3.6 Discusión de resultados

**Ganancia sobre el azar:** Con 14 clases, un clasificador aleatorio obtendría accuracy ≈ 7.1%. El RF alcanza 0.7723 (media CV), representando **10.8× el azar**. El F1-macro 0.7698 confirma que esta ganancia es real incluso en clases minoritarias.

**Estabilidad del estimador:** La std de 0.014 (Accuracy) y 0.016 (F1-macro) entre folds representa un CV% de ~1.9% y ~2.1% respectivamente — variabilidad baja para 14 clases con evaluación sobre donantes no vistos.

**Validación cruzada vs. split único:** La media CV (0.7723) es prácticamente idéntica al resultado de Etapa 3 (0.7740), diferencia < 0.002. Esto confirma que el split único de Etapa 3 no fue una partición favorablemente sesgada.

**Interpretación biológica de las confusiones:** Los errores del clasificador revelan qué regiones comparten perfiles transcriptómicos. Putamen ↔ Caudate (ambos ganglios basales), Cerebellum ↔ Cerebellar Hemisphere, Amygdala ↔ Hippocampus — confusiones anatómicamente coherentes que son información científica, no solo fallos del modelo.

**Firmas moleculares estables entre individuos:** La alta consistencia de la importancia de PCs entre folds (mismos PCs dominantes en los 5 folds) confirma que el modelo aprende firmas biológicas del tipo celular, no características de donantes específicos. Esto es la condición necesaria para el uso del modelo como línea base en medicina espacial.

---

## 4. Conclusiones y trabajo futuro

### 4.1 Conclusiones

1. **Clasificación robusta de regiones cerebrales:** El modelo Random Forest clasifica correctamente el 77.2% de las muestras de tejido nervioso por su región de origen, generalizando a donantes completamente nuevos. Esta accuracy, significativamente superior al azar (7.1%), valida que los patrones transcriptómicos por región cerebral son propiedades del tipo celular, no artefactos del individuo.

2. **Validez estadística confirmada por CV:** La validación cruzada de 5 pliegues (GroupKFold por donante) con Accuracy media 0.7723 ± 0.014 y F1-macro 0.7698 ± 0.016 demuestra que los resultados de Etapa 3 no eran una casualidad estadística, sino la capacidad real del modelo.

3. **Factibilidad del pipeline Big Data:** La estrategia de carga por bloques (chunked reading), selección por varianza, PCA en sklearn, y entrenamiento distribuido en PySpark permitió procesar el dataset GTEx V10 (~4.7 GB) en hardware de escritorio en tiempo razonable.

4. **Confusiones biológicamente interpretables:** Los errores del clasificador entre regiones anatómicamente próximas (ganglios basales, cortezas cerebrales) son información científica sobre la similitud transcriptómica de esas regiones — no pueden eliminarse con más datos ni con algoritmos más complejos sin información adicional (p.ej., metilación del ADN, proteómica).

5. **Línea base establecida para medicina espacial:** El modelo entrenado sobre GTEx V10 constituye un punto de referencia cuantitativo del transcriptoma cerebral humano sano. Muestras de astronautas post-vuelo que clasifiquen incorrectamente o con baja probabilidad de clase son candidatos a presentar alteraciones transcriptómicas inducidas por microgravedad o radiación.

### 4.2 Trabajo futuro

1. **Desbalance de clases:** Implementar `ClassWeightedRandomForestClassifier` o técnicas de oversampling (SMOTE) para mejorar la precisión en regiones minoritarias (Amygdala, Substantia nigra).

2. **Ajuste fino de hiperparámetros:** Aplicar `CrossValidator` de PySpark MLlib con `GroupKFold` para buscar automáticamente `numTrees`, `maxDepth` y `featureSubsetStrategy` óptimos.

3. **Modelos alternativos:** Comparar con Gradient Boosted Trees (mayor precisión potencial) y redes neuronales MLP (captura de interacciones no lineales entre genes), ambos disponibles en PySpark MLlib.

4. **Features adicionales:** Incorporar variantes genéticas (SNPs) del proyecto GTEx para controlar la variabilidad inter-individual y mejorar la generalización.

5. **Aplicación a datos de astronautas:** Obtener datos de expresión génica de estudios NASA (p.ej., NASA GeneLab) y aplicar el modelo GTEx como clasificador, detectando muestras que "no pertenecen" a ninguna región conocida (detección de anomalías transcriptómicas).

6. **Clustering jerárquico:** Reemplazar K-Means por clustering espectral o HDBSCAN para capturar la estructura no convexa del espacio transcriptómico cerebral en PCA(50).

---

## 5. Referencias

1. Breiman, L. (2001). Random Forests. *Machine Learning*, 45(1), 5–32.
2. GTEx Consortium. (2020). The GTEx Consortium atlas of genetic regulatory effects across human tissues. *Science*, 369(6509). https://doi.org/10.1126/science.aaz1776
3. GTEx Portal. (2025). GTEx Analysis V10 Downloads. Broad Institute. https://gtexportal.org/home/downloads/adult-gtex
4. Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The Elements of Statistical Learning* (2nd ed.). Springer.
5. Kohavi, R. (1995). A study of cross-validation and bootstrap for accuracy estimation and model selection. *IJCAI-95*, 1137–1143.
6. Law, C. W., Chen, Y., Shi, W., & Smyth, G. K. (2016). voom: Precision weights unlock linear model analysis tools for RNA-seq read counts. *Genome Biology*, 17, 29.
7. Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR*, 12, 2825–2830.
8. Scott, R. T., et al. (2019). Molecular muscle experiments with omics observations (MMEO). *npj Microgravity*, 5(1), 1–10.
9. Zaharia, M., et al. (2016). Apache Spark: A Unified Engine for Big Data Processing. *CACM*, 59(11), 56–65.

---

## Declaración de uso de Inteligencia Artificial

Anthropic. (2026). *Claude Sonnet 4.6* [Modelo de lenguaje grande], utilizado como asistente en la estructuración del reporte, revisión de código PySpark y redacción de secciones de documentación. https://claude.ai

*Las decisiones de diseño experimental, interpretación de resultados y conclusiones son responsabilidad del autor.*
