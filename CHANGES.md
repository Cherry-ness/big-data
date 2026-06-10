# Registro de cambios — Etapa 4

## Branch `etapa4`

### Objetivo
Entrega final del proyecto: documento técnico completo + notebook maestro con pipeline end-to-end ejecutado.

### Archivos creados
- `etapa4_reporte_tecnico.md` — reporte técnico en markdown
- `etapa4_notebook.ipynb` — notebook maestro ejecutado con outputs reales

---

### `etapa4_reporte_tecnico.md`

Documento técnico con las secciones requeridas por la rúbrica:

- Título, resumen, introducción
- Propuesta de solución (7 subsecciones): dataset GTEx V10, construcción de muestra M, selección de features por varianza, preprocesamiento (StandardScaler + PCA), métricas, modelos supervisado/no supervisado, estrategia de validación
- Experimentación: todos los resultados numéricos (tabla de folds, matriz de confusión resumida, importancia de PCs, K-Means)
- Conclusiones y trabajo futuro
- Referencias (7 fuentes)
- Declaración de uso de IA
- Placeholder para video: `> **Video explicativo:** [Enlace al video — YouTube/Drive]`

---

### `etapa4_notebook.ipynb`

Notebook maestro con 32 celdas cubriendo el pipeline completo:

| Sección | Contenido |
|---------|-----------|
| 1. Setup | PySpark `local[*]`, 8 GB driver, semilla 42, `matplotlib.use('Agg')` |
| 2. Metadatos GTEx | Carga de `SampleAttributes` + `SubjectPhenotypes`, filtro RNASEQ, SUBJID por regex |
| 3. Muestra M | 10 particiones: 5 TISSUE_GROUP × 2 SEX_LABEL, gráfica de distribución |
| 4. Varianza | Lectura chunked 500 genes/bloque sobre 59,033 genes (~4.7 GB), top-500 seleccionados |
| 5. M_nervioso | 3,904 muestras, 786 donantes, 14 clases SMTSD; StandardScaler → PCA(50, 87% varianza) |
| 6. Métricas y algoritmos | Justificación de Accuracy, F1-macro, Silhouette; hiperparámetros RF |
| 7. RF 5-fold CV | `GroupKFold` por SUBJID, loop PySpark MLlib `RandomForestClassifier(numTrees=100, maxDepth=10)` |
| 8. K-Means | k=2..12, método del codo con Silhouette + WCSS en PySpark MLlib |
| 9. Visualizaciones | 8 gráficas guardadas en `src/preliminary-analysis/etapa4_*.png` |
| 10. Conclusiones | Análisis, trabajo futuro, referencias |

#### Ejecución
```
conda run -n big-data jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=7200 etapa4_notebook.ipynb
```
- Exit code: 0
- Duración: ~30 min (5 RF + 11 K-Means en PySpark)
- Notebook resultante: 63,900 bytes con outputs reales en cada celda

---

### Visualizaciones generadas (`src/preliminary-analysis/`)

| Archivo | Descripción |
|---------|-------------|
| `etapa4_particiones_M.png` | Distribución de M (10 particiones TISSUE_GROUP × SEX) |
| `etapa4_variance_selection.png` | Histograma de varianza + top-20 genes por varianza |
| `etapa4_pca_variance.png` | Varianza explicada por componente + acumulada PCA(50) |
| `etapa4_cv_results.png` | Accuracy y F1 por fold con referencia Etapa 3 |
| `etapa4_confusion_matrix.png` | Matriz de confusión normalizada promedio 5 folds |
| `etapa4_per_class_metrics.png` | Precision/Recall/F1 por clase + CV% de variabilidad |
| `etapa4_feature_importance.png` | Importancia de PCs + heatmap de consistencia entre folds |
| `etapa4_kmeans_elbow.png` | Silhouette y WCSS vs k (k=2..12) |
| `etapa4_summary_panel.png` | Panel resumen: boxplot métricas, train vs test, Silhouette |

---

### Resultados principales

| Modelo | Métrica | Valor |
|--------|---------|-------|
| RF 5-fold CV | Accuracy | 0.7723 ± 0.014 |
| RF 5-fold CV | F1-macro | 0.7698 ± 0.016 |
| Referencia Etapa 3 | Accuracy | 0.7740 |
| K-Means | k óptimo | 2 |
| K-Means | Silhouette | 0.6022 |

---

### Pendiente

Agregar enlace del video en `etapa4_reporte_tecnico.md`:
```markdown
> **Video explicativo:** [Enlace al video — YouTube/Drive]
```
