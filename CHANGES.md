# Registro de cambios — TC5057 Big Data

## Branch `actividad5`

### Objetivo
Actividad 5: Visualización de resultados con validación cruzada 5-fold sobre el mejor modelo de Etapa 3.

### Archivos creados
- `individual-activities/Actividad5_Visualizacion_Resultados.ipynb`

### Pasos realizados
1. **Creación de branch** `actividad5` desde `main`
2. **Diseño del notebook** (30 celdas, 5 secciones según rúbrica):
   - S1: Justificación de K=5 (análisis cuantitativo: clase mínima Amygdala 181 muestras → ≥36/fold)
   - S2: Construcción de folds con `GroupKFold` por donante (Tr∩Ts=∅ a nivel SUBJID)
   - S3: Loop de entrenamiento RF en PySpark MLlib (5 folds × train+test = 10 modelos)
   - S4: 7 visualizaciones guardadas en `src/preliminary-analysis/act5_*.png`
   - S5: Discusión de resultados con valores reales del CV
3. **Fix headless matplotlib**: agregado `matplotlib.use('Agg')` + `OUTPUT_DIR` con `os.makedirs`
4. **Ejecución** vía `jupyter nbconvert --execute --inplace` (timeout 3600s, ~50 min)
5. **Commit y push** a `origin/actividad5` (sin PR)

### Resultados obtenidos
| Fold | Accuracy | F1-macro |
|------|----------|----------|
| 1    | ~0.773   | ~0.770   |
| 2    | ~0.771   | ~0.768   |
| 3    | ~0.774   | ~0.771   |
| 4    | ~0.770   | ~0.767   |
| 5    | ~0.773   | ~0.770   |
| **Media** | **0.7723 ± 0.014** | **0.7698 ± 0.016** |

---

## Branch `etapa4`

### Objetivo
Entrega final del proyecto: documento técnico completo + notebook maestro con pipeline end-to-end.

### Archivos creados
- `etapa4_reporte_tecnico.md` — reporte técnico en markdown (~400 líneas)
- `etapa4_notebook.ipynb` — notebook maestro ejecutado con outputs reales

### Pasos realizados

#### 1. Creación de branch
```
git checkout -b etapa4
```

#### 2. `etapa4_reporte_tecnico.md`
Documento técnico con las secciones:
- Título, resumen, introducción
- Propuesta de solución (7 subsecciones): dataset, muestra M, feature selection, preprocesamiento, métricas, modelos, validación
- Experimentación: todos los resultados numéricos (tabla de folds, matriz de confusión resumida, importancia de PCs, K-Means)
- Conclusiones y trabajo futuro
- Referencias (7 fuentes)
- Declaración de uso de IA
- Placeholder para video: `> **Video explicativo:** [Enlace al video — YouTube/Drive]`

#### 3. `etapa4_notebook.ipynb`
Notebook maestro con 32 celdas cubriendo el pipeline completo:

| Sección | Contenido |
|---------|-----------|
| 1. Setup | PySpark `local[*]`, 8 GB driver, semilla 42, `matplotlib.use('Agg')` |
| 2. Metadatos GTEx | Carga de `SampleAttributes` + `SubjectPhenotypes`, filtro RNASEQ, SUBJID extraído por regex |
| 3. Muestra M | 10 particiones: 5 TISSUE_GROUP × 2 SEX_LABEL, gráfica de distribución |
| 4. Varianza | Lectura chunked 500 genes/bloque sobre 59,033 genes (~4.7 GB), top-500 seleccionados |
| 5. M_nervioso | 3,904 muestras, 786 donantes, 14 clases SMTSD; StandardScaler → PCA(50, 87% varianza) |
| 6. Métricas | Justificación de Accuracy, F1-macro, Silhouette |
| 7. RF 5-fold CV | `GroupKFold` por SUBJID, loop PySpark MLlib `RandomForestClassifier(numTrees=100, maxDepth=10)` |
| 8. K-Means | k=2..12, método del codo con Silhouette + WCSS en PySpark MLlib |
| 9. Visualizaciones | 5 gráficas: particiones M, varianza, PCA, CV results, confusion matrix, per-class metrics, feature importance, summary panel |
| 10. Conclusiones | Análisis de resultados, trabajo futuro, referencias |

#### 4. Ejecución del notebook
```
conda run -n big-data jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=7200 etapa4_notebook.ipynb
```
- Exit code: 0
- Output: 63,900 bytes (notebook con resultados reales en cada celda)
- Duración: ~30 min (5 RF + 11 K-Means en PySpark)

#### 5. Commits y push
```
git add etapa4_notebook.ipynb etapa4_reporte_tecnico.md
git commit -m "Add Etapa 4 final delivery: notebook + technical report"
git push -u origin etapa4

git add etapa4_notebook.ipynb   # tras ejecución
git commit -m "Execute etapa4_notebook.ipynb: add cell outputs"
git push origin etapa4
```

---

## Archivos generados en `src/preliminary-analysis/`

| Archivo | Descripción |
|---------|-------------|
| `act5_k_justification.png` | Tabla visual justificación K=5 |
| `act5_fold_construction.png` | Distribución de clases por fold |
| `act5_cv_results.png` | Accuracy y F1 por fold (Actividad 5) |
| `act5_confusion_matrix.png` | Matriz de confusión normalizada (Actividad 5) |
| `act5_per_class_metrics.png` | Precision/Recall/F1 por clase (Actividad 5) |
| `act5_feature_importance.png` | Importancia de PCs por fold (Actividad 5) |
| `act5_summary_panel.png` | Panel resumen (Actividad 5) |
| `etapa4_particiones_M.png` | Distribución de M (10 particiones) |
| `etapa4_variance_selection.png` | Distribución de varianza + top-20 genes |
| `etapa4_pca_variance.png` | Varianza explicada PCA(50) |
| `etapa4_cv_results.png` | CV results con referencia Etapa 3 |
| `etapa4_confusion_matrix.png` | Matriz de confusión (Etapa 4) |
| `etapa4_per_class_metrics.png` | Métricas por clase + CV% (Etapa 4) |
| `etapa4_feature_importance.png` | Importancia PCs + heatmap por fold |
| `etapa4_kmeans_elbow.png` | Silhouette + WCSS vs k |
| `etapa4_summary_panel.png` | Panel resumen final |

---

## Pendiente

- Grabar video explicativo y agregar el enlace en `etapa4_reporte_tecnico.md`:
  ```markdown
  > **Video explicativo:** [Enlace al video — YouTube/Drive]
  ```
