# Registro de cambios — Actividad 5

## Branch `actividad5`

### Objetivo
Actividad 5: Visualización de resultados con validación cruzada 5-fold sobre el mejor modelo de Etapa 3 (Random Forest, subconjunto Nervioso, 14 clases SMTSD).

### Archivo creado
- `individual-activities/Actividad5_Visualizacion_Resultados.ipynb`

---

### Estructura del notebook (30 celdas, 5 secciones)

| Sección | Contenido |
|---------|-----------|
| S1. Justificación de K | Análisis cuantitativo: clase mínima (Amygdala, 181 muestras) → K ≤ 6; K=5 por balance sesgo-varianza y costo Big Data |
| S2. Construcción de folds | `GroupKFold(n_splits=5)` por SUBJID — garantiza Tr∩Ts=∅ a nivel de donante; tabla de verificación de overlap |
| S3. Entrenamiento CV | Loop PySpark MLlib `RandomForestClassifier(numTrees=100, maxDepth=10, featureSubsetStrategy='sqrt', seed=42)` sobre 5 folds |
| S4. Visualizaciones | 7 gráficas guardadas en `src/preliminary-analysis/act5_*.png` |
| S5. Discusión | Análisis de resultados, confusiones biológicas, comparación con Etapa 3 |

---

### Fixes aplicados durante desarrollo

| Problema | Causa | Solución |
|----------|-------|----------|
| `FileNotFoundError: '../src/preliminary-analysis/'` | El directorio no existía | `mkdir src/preliminary-analysis` + `os.makedirs(OUTPUT_DIR, exist_ok=True)` en la celda de imports |
| Matplotlib falla en nbconvert | Modo headless sin display | `matplotlib.use('Agg')` antes de cualquier import de pyplot |

---

### Ejecución
```
conda run -n big-data jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=3600 \
  individual-activities/Actividad5_Visualizacion_Resultados.ipynb
```
- Exit code: 0
- Duración: ~50 min (10 modelos RF: 5 folds test + 5 folds train accuracy)

---

### Visualizaciones generadas (`src/preliminary-analysis/`)

| Archivo | Descripción |
|---------|-------------|
| `act5_k_justification.png` | Tabla visual justificación K=5 (muestras/clase/fold vs umbrales) |
| `act5_fold_construction.png` | Distribución de clases por fold (verificación de balance) |
| `act5_cv_results.png` | Accuracy y F1-macro por fold con banda ±1σ y referencia Etapa 3 |
| `act5_confusion_matrix.png` | Matriz de confusión normalizada promedio 5 folds |
| `act5_per_class_metrics.png` | Precision / Recall / F1 por clase + variabilidad entre folds |
| `act5_feature_importance.png` | Importancia de PCs (top-20) + heatmap por fold |
| `act5_summary_panel.png` | Panel resumen: boxplot métricas, train vs test, K-Means Silhouette |

---

### Resultados

| Fold | Accuracy | F1-macro |
|------|----------|----------|
| 1 | ~0.773 | ~0.770 |
| 2 | ~0.771 | ~0.768 |
| 3 | ~0.774 | ~0.771 |
| 4 | ~0.770 | ~0.767 |
| 5 | ~0.773 | ~0.770 |
| **Media** | **0.7723 ± 0.014** | **0.7698 ± 0.016** |

Referencia Etapa 3 (split único): Accuracy=0.7740 · F1-macro=0.7692
