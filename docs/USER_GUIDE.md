# FloodML-Geo 0.3 – User guide

*Developed by **Md Mominul Islam**.*

Flood-susceptibility modelling in QGIS with machine learning, honest spatial validation, publication-quality figures and ready-styled maps.

**Contents**

1. [What you get](#1-what-you-get)
2. [Install the plugin in QGIS](#2-install-the-plugin-in-qgis)
3. [Install the Python packages](#3-install-the-python-packages)
4. [Check that it works – the self-test](#4-check-that-it-works--the-self-test)
5. [Prepare your data](#5-prepare-your-data)
6. [Quick start (15 minutes)](#6-quick-start)
7. [Tool 01 – Build the training table](#7-tool-01--build-the-training-table)
8. [Tool 02 – Quality check](#8-tool-02--quality-check)
9. [Tool 03 – Train and validate](#9-tool-03--train-and-validate)
10. [Tool 04 – Map susceptibility](#10-tool-04--map-susceptibility)
11. [Tool 05 – Independent test](#11-tool-05--independent-test)
12. [Reading the report and the figures](#12-reading-the-report-and-the-figures)
13. [Recommended settings for a thesis or paper](#13-recommended-settings-for-a-thesis-or-paper)
14. [Troubleshooting](#14-troubleshooting)
15. [Limits and interpretation](#15-limits-and-interpretation)
16. [Running it from the Python console](#16-running-it-from-the-python-console)

---

## 1. What you get

The workflow follows the tool numbers:

```
 flood record raster (0/1)  = TARGET ─┐
 predictor rasters (elevation, …)  ───┼─►  01 Build the training table ─► CSV (flood, x, y, elevation, …)
 points  OR  grid polygons (where) ───┘                                       │
                                                                              ▼
                       02 Quality check ─► 03 Train + validate ─► 04 Map ─► 05 Independent test
                       06 Self-test (checks that all of this works)
```

Seven tools appear in the **Processing Toolbox** under **FloodML-Geo**:

| Tool | Purpose |
|---|---|
| **01 Build the training table** | The **flood record raster (0 = no flood, 1 = flood)** is added like a predictor raster, but it becomes the **target** column `flood`; all other rasters become predictors. **Points** → every raster is read directly at the point. **Grid polygons** → zonal mean of every predictor (majority for categorical) and the **flooded share** of the cell for the target, with automatic virtual resampling when a raster pixel is larger than the cell. The points or grid need **no label field**. |
| **02 Quality check** | Finds problems *before* modelling: class imbalance, constant or label-leaking predictors, collinearity, missing values, degree coordinates, spatial clustering; suggests a block size. |
| **03 Train and validate** | Random Forest, XGBoost, LightGBM, HistGB, logistic regression. Fold-safe preprocessing, spatial cross-validation, optional nested tuning, bootstrap confidence intervals, importance, SHAP, HTML report, figures. |
| **04 Map flood susceptibility** | Susceptibility raster, ensemble spread, class map with area table, extrapolation map, automatic alignment of rasters with different grids, ready `.qml` styles, preview image. |
| **05 Independent test** | Scores saved models on a second area / event / year, without refitting or tuning. |
| **06 Self-test** | Runs every tool on a built-in synthetic study area and compares the results with known answers. PASS / FAIL report. |
| **07 (Optional) Draw sample points from the flood raster** | Only if you have no points yet: draws balanced flood / non-flood pixel centres from the flood raster. |

A menu **Plugins → FloodML-Geo** gives the self-test, a dependency installer, this guide and an About box.

---

## 2. Install the plugin in QGIS

Requires **QGIS 3.28 or newer** (a recent LTR is best).

1. Download **`FloodML_Geo_QGIS_Plugin_v0.3.1.zip`**. Do **not** unzip it.
2. In QGIS: **Plugins → Manage and Install Plugins… → Install from ZIP**.
3. Click **…**, choose the ZIP, then **Install Plugin**. Confirm the security notice.
4. Switch to the **Installed** tab and make sure **FloodML-Geo** is ticked.
5. Open the Processing Toolbox with **Ctrl + Alt + T** (or *Processing → Toolbox*) and expand **FloodML-Geo**. If the Processing plugin is switched off, enable it under *Plugins → Manage and Install Plugins → Installed*.

You will see tools 01–07. If the *Plugins → FloodML-Geo* menu is missing, the plugin did not load: open *Plugins → Python Console* or *View → Panels → Log Messages → Plugins* and read the error (usually a missing Python package, see next section).

**Updating (or replacing an old 0.2.0 / 0.2.1):** in *Manage and Install Plugins → Installed* select **FloodML-Geo → Uninstall Plugin**, restart QGIS, then install the new ZIP as above and restart QGIS once more. Installing over the old version without a restart can leave the old code loaded.

---

## 3. Install the Python packages

FloodML-Geo needs scikit-learn and friends **inside the Python that QGIS uses**. Many QGIS installs already contain some of them. The plugin itself loads without them, and **tool 01 (building the training table), tool 07 and the menu need no extra package**; tools 02 – 06 do (06 runs step 01 without them and tells you what is missing).

### The easy way (all systems)

**Plugins → FloodML-Geo → Check / install Python dependencies…** shows what is installed and has an **Install missing packages** button. Restart QGIS when it says *Finished (exit code 0)*.

Required: `numpy, pandas, scipy, scikit-learn, joblib, matplotlib`. Optional: `xgboost` (XGBoost model), `lightgbm` (LightGBM model), `shap` (SHAP figures).

### Windows (QGIS from the OSGeo4W or standalone installer)

If the button fails (no permission, proxy …):

1. Start menu → **OSGeo4W Shell** → *Run as administrator* (for the standalone installer it is the same shell, installed together with QGIS).
2. Type:
   ```
   python -m pip install --upgrade pip
   python -m pip install scikit-learn pandas scipy joblib matplotlib xgboost lightgbm shap
   ```
3. Restart QGIS.

### macOS (QGIS.app)

In Terminal:
```
/Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install scikit-learn pandas scipy joblib matplotlib xgboost lightgbm shap
```
(If your QGIS app has a different name, adjust the path.)

### Linux

Debian / Ubuntu with the distribution's QGIS:
```
sudo apt install python3-sklearn python3-pandas python3-scipy python3-matplotlib python3-joblib
python3 -m pip install --user --break-system-packages xgboost lightgbm shap
```
Other systems: `python3 -m pip install --user scikit-learn pandas scipy joblib matplotlib xgboost lightgbm shap`.

### If the buttons and the shell do not work – use QGIS itself

*Plugins → Python Console*, paste:
```python
import subprocess
from floodml_geo.core import deps
cmd = deps.pip_command(['scikit-learn','pandas','scipy','joblib','matplotlib','xgboost','lightgbm','shap'])
print(' '.join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout[-3000:], r.stderr[-3000:])
```
Restart QGIS afterwards.

> **Note** Installing a package can upgrade `numpy`. If QGIS complains about numpy after an installation, install a numpy version that matches your QGIS build, e.g. `python -m pip install "numpy<2"`.

---

## 4. Check that it works – the self-test

Run this once after installing, and again whenever something looks wrong.

**Plugins → FloodML-Geo → Run self-test …** (or Processing Toolbox → FloodML-Geo → **06 Self-test**) → **Run**. Optionally tick *Also test XGBoost, LightGBM and SHAP*. It takes one to three minutes, uses **no data of yours** and writes only into its output folder (a temporary folder if you leave it empty).

It builds a small synthetic study area (predictor rasters with 30 m, 100 m and 1500 m cells, a **flood record raster** with 0/1 pixels, random points and a 500 m grid – the points and the grid have **no label at all**) and then runs the real tools in the real order, comparing every result with a known answer:

| Step | What is verified |
|---|---|
| Environment | QGIS, GDAL and the Python packages are present. |
| 01 points + flood raster | The `flood` column equals the flood-raster pixel under every point; elevation is the direct pixel value; land-cover codes are intact; the metadata sidecar is right. |
| 01 grid cells + flood raster | The flood share of every cell equals the exact average of its 5 × 5 flood pixels; a 1500 m raster under 500 m cells reproduces a linear surface exactly (resampling works); a 30 m raster is averaged correctly. |
| 01 safeguards | The flood raster as a predictor is **refused**; a table with only flooded points is **refused**. |
| 02 quality check | Report written, no blocking problem on a clean table. |
| 03 train + validate | Models reach a cross-validated AUC above 0.7; report and ≥ 8 figures written. |
| 04 susceptibility map | Values within 0–1, rasters with three different grids aligned, class table sums to 100 %, the `.qml` styles load in QGIS. |
| 05 independent test | Saved models score above chance on a second point set. |
| 07 helper | Drawn points carry the right labels; tool 01 reads them back. |

The log shows `[PASS]` or `[FAIL]` per step and the end says **SELF-TEST PASSED: everything works.** An HTML report `selftest_report.html` in the output folder lists every step and the installed package versions. If a step fails, the message tells you what was wrong (for example *Python packages missing: scikit-learn*); send the report to whoever supports you.

The self-test is itself tested: the package's own test suite sabotages a tool on purpose and checks that the self-test then says FAILED. The scores on synthetic data are a test of the *mechanics*, not a scientific result.

---

## 5. Prepare your data

You need:

* **A flood record raster** – one raster where **1 = flooded and 0 = not flooded** (for example the mapped extent of a past event, rasterised). It is the **target variable**: it goes into tool 01 in its own box, next to – but separate from – the predictor rasters. If your map only has values on flooded pixels and dry land is NoData, tick *read NoData as no flood* (advanced option); if "flood" is stored as another value (255 …) set *pixel value that means flood*.
* **Locations** – either a **point** layer or a **polygon grid** (for example 500 m or 1 km cells). These layers only say *where* to read the rasters; they need **no flood label field**. For points, make sure both flooded and dry places are included (the flood raster supplies the 0/1 at every point). A grid covering the whole study area gives both classes automatically. No points yet? Tool 07 can draw balanced points from the flood raster.
* **Predictor rasters** – elevation, slope, rainfall, distance to river, land cover … They may have **different cell sizes, extents and CRSs**; tool 01 handles that. Local GeoTIFF files (or anything GDAL reads from disk). Each raster must be georeferenced, north-up (not rotated).
* *(optional)* A **group / event ID** field: records that belong together (same flood event, same polygon cut into pieces, same site visited repeatedly). They will always stay in the same validation fold.

Good practice before you start:

1. **Name the raster layers** in the *Layers* panel exactly as you want the predictor names: `elevation`, `slope`, `rainfall`, `dist_river`, `landcover`. The tool lower-cases the name and turns spaces and symbols into `_`. These names are what tool 04 matches later.
2. Use a **projected CRS in metres** for the points / grid if possible (e.g. WGS 84 / UTM 46N for Sylhet). If your layer is in degrees the tool computes x/y in the matching UTM zone automatically.
3. Include **non-flood** records that are representative of the area (not only the easiest dry places) and from the same period and accuracy as the flood records.
4. Use only predictors known **before** the flood. Never use a layer derived from the flood extent or from post-event imagery. The flood record raster is the target: tool 01 refuses to take it as a predictor as well.

---

## 6. Quick start

1. **Load** the flood record raster, the predictor rasters and your point layer *or* grid layer in QGIS. Rename the predictor rasters (`elevation`, `slope`, …).
2. *(First time only)* **Plugins → FloodML-Geo → Run self-test** and wait for **SELF-TEST PASSED**.
3. **01 Build the training table** – *Points OR grid polygons*: your layer. *Flood record raster = TARGET*: the 0/1 raster. *Predictor rasters*: tick all predictors (**not** the flood raster); tick the land-cover raster also under *Categorical rasters*. Set *Training table (CSV)* to a file, **Run**. Check the log: how many flood / non-flood records, how many cells were resampled finer.
4. **02 Quality check** – pick the CSV, choose an output folder, **Run**. Open `dataset_report.html`. Fix every item marked *BLOCKING*.
5. **03 Train and validate** – pick the CSV, models (start with *Random Forest* + *Logistic regression*), *Validation design = Spatial blocks*, folds 5, block size 0 (automatic). In *Directions* you may type `elevation:reverse, rainfall:positive`. **Run**. Open `report.html`.
6. **04 Map flood susceptibility** – pick `RF_model.joblib` (click **…** and add the file; several models give an ensemble), the rasters, keep *Align rasters automatically* ticked, choose *Classified map = Quantile*, save the raster. The result opens already styled.
7. *(Strongly recommended for a paper)* **05 Independent test** with a second dataset.

---

## 7. Tool 01 – Build the training table

**Where does the flood record raster (0/1) go?** Into its own box in tool 01, **Flood record raster = TARGET**. Tool 01 reads it exactly like a predictor raster – at your points or inside your grid cells – but writes the result to the column **`flood`**, the variable the models will learn to predict. All other rasters become predictor columns.

```
 flood_record.tif  (0/1) ───────────►  column  flood           ← target
 elevation.tif, rainfall.tif, … ────►  columns elevation, rainfall, …  ← predictors
 points  or  grid polygons  ────────►  where to read (no label field needed)
                                        ▼
                                  training.csv:  record_id, flood, x, y, elevation, rainfall, …
```

Creates the **raw** training table. Nothing is normalised, imputed or selected here: all of that happens later *inside each cross-validation fold*, which is what keeps the validation honest.

### Parameters

| Parameter | Meaning |
|---|---|
| **Points OR grid polygons** | Point or polygon layer: *where* to read. Multi-point features use their first point (a warning is given). |
| **Flood record raster = TARGET** | The 0/1 raster. Refused if the same raster is also among the predictors. Any CRS / cell size / extent. |
| **Predictor rasters** | All predictors. The **layer name** is the predictor name. |
| **Exclude places where this raster has the value … (optional)** | **Permanent water.** A river or lake is never "flooded" in a flood record, so without this option it becomes *non-flood* and the model learns "water = safe" (the river channel then appears as *Very low* susceptibility). Give a raster in which the value (default 1) marks open water or other places that cannot flood. Points on that value, and grid cells at least half covered by it, are left out of the table. Apply the same mask to the final map. |
| **Categorical rasters** | Subset of the predictors (land cover, soil, geology, …). They are **never interpolated or averaged**: points get the pixel class, polygons the **majority class**; tool 03 one-hot encodes them. |
| **Group / event ID field** | Optional; written as `group_id`. |
| **POINTS: how to read a predictor raster** | *Direct pixel value* (default) or *Bilinear* between the four nearest pixel centres. The flood label is **always** the pixel value (never interpolated). |
| **POLYGONS: resample finer…** | Switch for the automatic fine-resampling described below (default on). |
| **POLYGONS: a cell is "flood" when this share of it is flooded** | Default **0.5**. The cell gets `flood = 1` when the flooded share of its area is at least this value. |
| *Advanced:* flood-record value / NoData as no flood | Pixel value that means flood (default 1); read NoData *inside* the raster as "no flood" (for maps that store only the flooded pixels). |
| *Advanced:* label field | Only if you have **no** flood raster: an existing 0/1 field of the layer (use one or the other, never both). |
| *Advanced:* drop cells smaller than … of the median cell area | Grids clipped to a study-area boundary contain tiny edge cells whose values rest on a few pixels. 0 (default) keeps all and prints a warning when such cells exist; 0.5 removes cells smaller than half of the median cell area. |
| *Advanced:* interpolation | Predictors only: bilinear (default, smooth) or nearest when resampling finer. The flood raster always uses nearest, so the flooded share stays exact. |
| *Advanced:* minimum samples across a cell | Default **8**. See below. |
| *Advanced:* minimum share of valid data | Default **0.5**: a cell is left blank if less than half of it is covered by valid (non-nodata) raster data. |
| *Advanced:* raster band | Band used from every predictor raster (default 1). |
| *Advanced:* metric CRS | CRS for `x`, `y` and cell sizes. Default: the layer CRS if it is in metres, else the matching UTM zone. |
| **Training table (CSV)** | Output. A `.metadata.json` (what was done, target and predictor lists, cell size, raster info, file hash) and a `.csvt` are written next to it. |
| **Layer with the extracted values** | Optional: the same records as a QGIS layer, to inspect or map the extracted values. |

Output columns: `record_id, flood, x, y, [group_id], <predictors…>` (**`flood`** is the 0/1 target column) and, for grid polygons, `flood_fraction` (the flooded share of the cell, 0–1; information only, never used as a predictor) and `extract_min_valid_fraction` (QA only).

### How the flood label is obtained

| Locations | Flood label |
|---|---|
| **Points** | The value of the flood-record pixel that contains the point (0 or 1). Never interpolated. A point outside the flood raster, or on NoData, has no label and is **dropped** (counted in the log). |
| **Grid polygons** | The **flooded share** of the cell: area-weighted mean of the 0/1 pixels inside the exact cell outline (written as `flood_fraction`). `flood = 1` when the share is ≥ the threshold (default 0.5). A cell smaller than the flood-raster pixel is resampled onto a finer lattice (nearest neighbour), so the share stays exact; a cell larger than the pixel uses all pixels inside it. A cell with too little valid flood-raster coverage has no label and is dropped. |

Refusals (with a clear message, nothing is written): the flood raster is also a predictor; the flood raster holds values other than 0 and the flood value (the message lists them); only one class would remain (for example every point lies on a flooded pixel – draw dry points too, use a grid, or use tool 07).

### How predictor values are obtained for points (direct extraction)

Each raster is read **directly at the point**: the value of the pixel that contains the point (or a bilinear blend if you choose it). Points outside the raster or on nodata give a blank. Rasters in another CRS are handled: the point is transformed to the raster's CRS first.

### How predictors are obtained for grid polygons (zonal mean, with careful resampling)

For every cell and every raster the tool takes the **area-weighted mean** of the raster inside the exact cell outline (holes and multipart cells are respected). It does this with a regular lattice of sample points over the cell, aligned with the raster's pixels:

| Situation | What happens |
|---|---|
| **Pixel smaller than the cell** (e.g. 30 m DEM, 500 m cell) | Ordinary zonal mean: every pixel in the cell contributes, edge pixels in proportion to the part inside the cell. |
| **Pixel about as large as, or larger than, the cell** (e.g. 1 km rainfall, 500 m cell) | The raster is **resampled virtually to a finer grid** so that at least **8 samples** span each cell side (the integer sub-division `k` of the native pixel is chosen per cell). With bilinear interpolation a smooth surface is obtained, the mean is that of the *finer* surface. **No giant temporary raster is created**, and the result does not depend on how the cell happens to fall on the coarse pixels. |
| **Categorical raster** | Nearest value only (never blended); the **majority** class inside the cell. |
| **Raster in a different CRS** | Cell outlines are densified and reprojected to the raster CRS (the log says so). |
| **Raster smaller than the study area / nodata** | Cells with < 50 % valid coverage are left blank; the log counts them. |

The log reports for every raster how many cells had to be resampled finer, the median cell size in pixels, how many cells fell outside the raster, and how many were blank. The same numbers are stored in the `.metadata.json`.

> **Interpolation caveat.** Resampling a coarse raster finer *adds no new information*; it only avoids the artefact of counting a single coarse pixel as the cell value. If the raster is much coarser than the cell, treat that predictor with care in the discussion of your results.

Rows with **no** predictor value at all (outside every raster) are dropped (count in the log). Rows that miss only some predictors are kept and median-imputed later inside each training fold (tool 02 lists them).

### Optional tool 07 – draw sample points from the flood raster

You do **not** need it in the normal workflow. Use it only when you have no points and want a ready, balanced set of locations: *N flood points* from the flooded pixels and *ratio × N* non-flood points from the dry pixels, with an optional minimum distance (use at least the pixel size of your coarsest predictor), a seed, and options for NoData and other pixel values. Give the resulting point layer to tool 01 together with the same flood raster. Scores then reflect that sampling ratio (balanced by default), not the real flood prevalence.

---

## 8. Tool 02 – Quality check

Run it on the CSV from tool 01 (or your own table), **before** training. It writes `dataset_report.html`, CSV tables and figures to the output folder and prints the verdict in the log.

* **Blocking** (shown as warnings): one class only; fewer than 10 minority records per fold; constant predictor; text in a numeric predictor; blank or degree coordinates.
* **Advice**: class imbalance, > 5 % missing values, single predictor with AUC ≥ 0.97 (possible leakage), VIF ≥ 10 or |ρ| ≥ 0.9, duplicated locations, many or rare categories, clustered labels (Moran's I) and a **suggested block size**.

Leave *Predictors* empty to use all predictors recorded by tool 01.

---

## 9. Tool 03 – Train and validate

### Parameters

| Parameter | Meaning |
|---|---|
| **Training table (CSV)** | From tool 01. The `.metadata.json` next to it is read automatically (predictors, categorical rasters, cell size). |
| **Predictor columns** | Empty = all from tool 01. Otherwise a comma list. The target `flood` and `flood_fraction` can never be predictors. |
| **Directions** | `name:positive` (higher → more susceptible, e.g. rainfall), `name:reverse` (e.g. elevation, distance to river), others unscaled. Scaling uses the **training fold's** min and max. Tree models do not enforce this relationship. |
| **Categorical predictors** | Empty = from tool 01. |
| **Models** | Random Forest · XGBoost · LightGBM · HistGB · Logistic regression (a useful baseline). |
| **Validation design** | **Spatial blocks** (recommended) · **spatial clusters** (k-means on x/y) · **group / event ID** · random stratified (comparison only; usually optimistic). |
| **Number of folds** | 5 is a good default. |
| **Spatial block size (m)** | **0 = automatic**: the median autocorrelation range of the label and predictors (semivariogram), capped so that enough blocks exist. Typical 3–30 km; look at the variogram figure. |
| **Group column** | Empty = `group_id` if present. Linked records never cross folds, even when they lie in different blocks. |
| **Tune hyper-parameters** | Nested random search inside each outer training set (slower, no leakage). |
| **Permutation importance / SHAP / Moran's I** | Held-out permutation importance; SHAP (needs `shap`); spatial autocorrelation of out-of-fold residuals. |
| **Draw figures + HTML report** and **Figure formats** | PNG, plus vector PDF / SVG and TIFF for journals; *Advanced:* dpi (default 300). |
| *Advanced:* buffer | Removes training records within *d* m of the validation block (buffered CV). |
| *Advanced:* class weighting | `balanced` (default) or none. |
| *Advanced:* bootstrap | Replicates for 95 % intervals (default 300; 0 = off). |
| *Advanced:* threshold | Probability cut-off for class metrics (default 0.5). Fix it in advance. |
| *Advanced:* seed, cores | Reproducibility, speed. |

### Output folder

| Path | Content |
|---|---|
| `report.html` | **Open first.** Headline table with 95 % CIs, validation design, all figures, warnings, caveats. Works offline, can be emailed. |
| `models/<Model>_model.joblib` | Deployment models for tools 04 / 05. Only open files you made or trust. |
| `tables/` | `model_comparison.csv`, `fold_metrics.csv`, `out_of_fold_predictions.csv`, `permutation_importance_heldout.csv`, SHAP tables, `moran_oof_residuals.csv`, `spatial_autocorrelation_ranges.csv`, `training_data_used.csv`. |
| `figures/` | Per model: ROC, precision–recall, confusion matrix, calibration, score distribution, fold metrics, importance, SHAP summary + dependence, spatial diagnostics. Overall: model comparison, CV-folds map, autocorrelation / block-size figure. |
| `run_manifest.json` | Settings, data hash, package versions, normalisation, CV plan, warnings: everything to reproduce the run. |

---

## 10. Tool 04 – Map susceptibility

| Parameter | Meaning |
|---|---|
| **Model file(s)** | One or more `*_model.joblib`. Several → **ensemble mean**. Click **…** and add the files (several files = ensemble). |
| **Predictor rasters** | Layer name (or file name) must equal the predictor name. The log shows which raster was matched to which predictor. |
| **Align rasters automatically** | Warps every raster onto one grid. Resampling is chosen from the pixel-size ratio: **bilinear** (or **average** when the output pixel is > 1.5× larger than the source pixel) for continuous data, **nearest** (or **mode**) for categorical. Switched off, any difference in CRS, pixel size, origin or extent stops the run with an exact list of what differs. |
| **Reference raster** | Defines the output grid (CRS, extent, alignment). Default: the first predictor. |
| **Output cell size** | 0 = reference cell size. **If you trained on grid cells (e.g. 1 km), enter that size**: predictors then have the same support as in training. A warning is given if the map pixel is much finer than the training cells. |
| **Classified map** | None · Quantile (equal area) · Equal interval · Natural breaks (Jenks) · Custom (e.g. `0.2, 0.4, 0.6, 0.8`), 2–9 classes with labels Low … Very high. |
| **Optional outputs** | *Between-model spread* (standard deviation, needs ≥ 2 models), *Class map*, *Extrapolation map* (number of predictors outside the training range), *Class area table (CSV)*, *Preview PNG* (map with scale bar and north arrow). |

Outputs are GeoTIFF (NoData = −9999; class map NoData = 0) with `.qml` styles next to them, so they open in QGIS already coloured. Large rasters are processed in tiles.

**Read the map as a relative ranking.** The score depends on the flood / non-flood sampling ratio. It is not an annual probability, depth or risk.

---

## 11. Tool 05 – Independent test

Cross-validation on one dataset still reuses one region and one event. The honest test is a **second dataset**: another catchment, event or year.

1. Run **tool 01** for the independent area / event: its **flood record raster**, its points or grid, and the predictor rasters for that area / period with the **same raster layer names** as in training.
2. Run **tool 05**: the model file(s), the new CSV, an optional group column or bootstrap block size, a threshold (default 0.5, *not* tuned on the test data).

**The test table must not contain the training records.** If you give tool 05 the same CSV that you trained on, the models have already seen every record and the scores (ROC-AUC near 1.0) only show how well they remember. Tool 05 compares the coordinates (or predictor values) with the saved models and, when 20 % or more of the test records are identical to training records, prints **NOT INDEPENDENT** in the log and at the top of the report. Do not report such results. Models saved by versions before 0.3.1 cannot be checked.

Output: `independent_test_report.html`, metrics with confidence intervals next to the cross-validated values, a warning if the test score is much lower, the share of test records outside the training range, and the usual figures.

---

## 12. Reading the report and the figures

* **ROC-AUC** – ranking quality; 0.5 = chance. **PR-AUC** – more informative when flood records are rare. **TSS** (sensitivity + specificity − 1) and **MCC / kappa** – threshold-based skill. **Brier / ECE** – calibration quality.
* **Shown as `0.87 [0.82–0.91]`** – pooled out-of-fold value with a 95 % *cluster-bootstrap* interval (whole blocks resampled, so spatial dependence is respected).
* **Fold AUC dots** show how much the score varies from region to region. A large spread means the model transfers unevenly.
* **Calibration** – dots near the diagonal mean the scores behave like probabilities of *your sample*; the bars show the score distribution.
* **Permutation importance** – drop in held-out AUC when a predictor is shuffled; correlated predictors share importance. **SHAP** – how each predictor moves the prediction (deployment model; not causal).
* **Spatial diagnostics** – residual map and correlogram. Moran's I clearly above 0 means structure the predictors do not capture.
* **Variogram figure** – the range of spatial autocorrelation for each variable and the recommended block size.
* **Extrapolation raster** – 0 means inside the training range for all predictors; ≥ 1 means be careful.

All figures use one colour-blind-safe palette and journal column widths (89 / 135 / 183 mm). Choose *PDF* or *SVG* in tool 03 for editable vector text.

---

## 13. Recommended settings for a thesis or paper

1. Tool 01 with a **metric CRS**, the flood record raster as target, categorical rasters declared, a `group_id` for events.
2. Tool 02: resolve every blocking issue; note the Moran's I of the label.
3. Tool 03: **Spatial blocks**, block size from the advisor, 5 folds, models RF + XGBoost + LightGBM + Logistic regression (baseline), **permutation importance on**, **SHAP on** for the best model, bootstrap 1000, figures as **PNG + PDF**, tuning on if the data set is large enough.
4. Report the **pooled out-of-fold** table with CIs and the validation design (block size, folds, buffer). Do not select "the best model" from these numbers and then quote them as unbiased: confirm with **tool 05**.
5. Tool 04: ensemble of the models you trust, class map by **quantile** or **natural breaks**, **extrapolation map** shown next to the map.
6. Keep `run_manifest.json` and the CSV `.metadata.json` with the thesis data.

Before you trust a map, also check:

* **Permanent water** (rivers, lakes) is excluded in tool 01 and masked on the final map; otherwise the water channel is learned as "non-flood".
* **Nearly duplicate predictors** (for example NDVI and NDWI, Spearman ≈ ±0.98, VIF > 10): keep one, or accept that their importance is shared.
* **Image dates** of satellite predictors (NDVI, NDWI, SAR): they must be **before** the flood. An image taken during or after the event shows the flood itself and leaks the answer.
* **Block size**: if tool 02 says the block size was *capped* below the autocorrelation range, neighbouring blocks still share information; repeat tool 03 with a buffer (for example 500 m) or larger blocks and fewer folds, and compare the scores.
* **Units**: distance rasters in degrees work for the models but are hard to interpret; metres are better.
* **Class maps**: *Equal interval* cuts the score at 0.2, 0.4, … and, when most records are flood, puts most of the area into *Very high*. *Quantile* or *Natural breaks* rank the area relative to itself.

Use the checklist in `LEAKAGE_PREVENTION_CHECKLIST.md` for what only you can verify.

---

## 14. Troubleshooting

| Message / symptom | Fix |
|---|---|
| *Python packages missing in QGIS: scikit-learn …* | Section 3. Restart QGIS afterwards. Tool 01, tool 07 and the menu work without them; tools 02 – 06 need them. |
| *ModuleNotFoundError: No module named 'sklearn'* when QGIS starts (traceback through `extract.py → core.validation → splitters`) | You have the old 0.2.0 build. Uninstall it, restart QGIS, install the latest ZIP (section 2) and install the Python packages (section 3). From 0.2.1 on the plugin always loads; a missing package only produces a friendly message when you run tool 02 – 06. |
| *Model needs xgboost / lightgbm / shap* | Install the package (section 3) or untick that model / SHAP. |
| *The flood raster must contain only 0 (no flood) and 1 (flood). It also contains: …* | The flood record has other values (for example 255 for "no data" that is not declared, or 2). Declare the NoData value, set the right *flood value* (advanced), or reclassify the raster. |
| *The table would contain no non-flood record* | All your points fall on flooded pixels. Add dry points, use a grid polygon layer, or draw balanced points with tool 07. |
| *… is the flood record raster AND a predictor* | Untick the flood raster in the predictor list. The target can never be a predictor. |
| *Where does the flood label come from?* | Select the *Flood record raster*; or – without a raster – the label field in the advanced options. Never both. |
| *record(s) have no flood-record value … dropped* | Those points / cells lie outside the flood raster or on NoData. If dry land is NoData in your flood map, tick *read NoData as no flood* (advanced). |
| *Layer … is not a local GDAL raster* | Export WMS / online layers to GeoTIFF first. |
| *No raster matches predictor(s) …* (tool 04) | Rename the raster layers to the predictor names shown in the message. |
| *Rasters do not share one grid …* | Tick **Align rasters automatically**, or set a reference raster / cell size. |
| *Only N independent group(s) for K folds* | Reduce the block size or folds, or check that coordinates are in metres. A group ID that spans the whole study area merges all blocks: use a more local ID. |
| *Coordinates look like degrees* | Re-run tool 01 (it writes metric x/y) or reproject the points. |
| *Many cells blank / outside raster* (tool 01) | The raster does not cover the cells, or the CRS of the layer or raster is wrong. Check *Layer → Set CRS*. |
| *NOT INDEPENDENT: … % of the test records are identical to training records* (tool 05) | The test CSV is (partly) the training data. Build it from another area, event or year. |
| The river or lakes appear as *Very low* susceptibility on the map | Permanent water was labelled non-flood. Re-run tool 01 with the exclusion raster (permanent water) and mask the final map with the same raster. |
| Test AUC much lower than cross-validated AUC | The model does not transfer to the new area; look at the extrapolation share and the predictors' distributions (tool 02 on both tables). |
| Run is slow | Fewer models, no tuning, no SHAP, lower bootstrap, set *CPU cores*. SHAP samples at most 500 rows by default. |
| QGIS 4 / Qt6 | The plugin declares Qt6 support but has so far been tested on QGIS 3.34 only. Report problems with the log text. |

To see details, open the **Log** tab of the tool dialog (and *Processing → Results Viewer* for earlier runs).

---

## 15. Limits and interpretation

* Susceptibility ≠ probability, depth, velocity, duration or risk.
* Spatial CV measures transfer **within the study region**. Another catchment or year needs tool 05.
* Scores reflect the **sampling design** (how non-flood points were chosen). Poor non-flood sampling gives impressive but meaningless numbers.
* Predictor *direction* does not constrain tree models; SHAP and importance describe the model, not causes.
* Grid-polygon training and pixel-level mapping have different support; set the output cell size accordingly.
* Models are saved with *joblib* (pickle). Do not open model files from untrusted sources.
* Tested: unit and end-to-end tests with real GDAL and a headless QGIS 3.34 on Linux, plus the built-in self-test (tool 06) that you can run on your own installation. **Not yet tested by the developer:** the on-screen dialogs on your machine, Windows / macOS installations, QGIS 4 – tool 06 tells you whether the processing part works on yours.

---

## 16. Running it from the Python console

Every tool is a normal Processing algorithm, so it can be scripted or used in the Graphical Modeler:

```python
import processing
csv = '/data/train.csv'
rasters = ['/data/elevation.tif', '/data/rainfall.tif', '/data/landcover.tif']
# 01 flood record raster (target) + predictor rasters at points or grid cells -> CSV
processing.run('floodmlgeo:extract_predictors', {
    'INPUT': '/data/points_or_grid.gpkg',          # no label field needed
    'FLOOD_RASTER': '/data/flood_record.tif',      # 0 / 1  -> column "flood"
    'RASTERS': rasters, 'CATEGORICAL': ['/data/landcover.tif'], 'OUTPUT': csv})
# 02 quality check
processing.run('floodmlgeo:check_dataset', {'DATA': csv, 'OUTPUT': '/data/check'})
# 03 train + validate
res = processing.run('floodmlgeo:train_models', {
    'DATA': csv, 'DIRECTIONS': 'elevation:reverse, rainfall:positive',
    'MODELS': [0, 1], 'CV': 0, 'FOLDS': 5, 'BLOCK': 0, 'OUTPUT': '/data/run1'})
# 04 map
processing.run('floodmlgeo:predict_raster', {
    'MODELS': [res['MODEL_RF']], 'RASTERS': rasters,
    'ALIGN': True, 'RES': 1000, 'CLASSES': 1, 'NCLASS': 5, 'OUTPUT': '/data/susceptibility.tif'})
# 06 self-test
processing.run('floodmlgeo:selftest', {'FULL': False, 'OUTPUT': '/data/selftest'})
```
Model indices for `MODELS` in tool 03: 0 = RF, 1 = XGBoost, 2 = LightGBM, 3 = HistGB, 4 = LogReg.

---

*FloodML-Geo is developed by **Md Mominul Islam**.*
