# Changelog

## 0.3.1
- Tool 05 flags a test table that contains the training records ("NOT INDEPENDENT") and marks the report as not valid.
- Tool 01: optional exclusion raster for permanent water, and a filter for tiny clipped edge cells.

## 0.3.0
- The flood record raster (0/1) is an input of tool 01 and becomes the target column. Points and grids need no label field.
- Workflow renumbered: 01 table, 02 check, 03 train, 04 map, 05 independent test, 06 self-test, 07 helper.
- New self-test tool with known-answer checks.
- Exact zonal mean for cells finer than the raster.

## 0.2.x
- Plugin loads without scikit-learn.
- New extraction engine, spatial cross-validation with block-size advisor, bootstrap intervals, new figure system, HTML reports, raster auto-alignment, ensemble and extrapolation maps, QML styles, dependency installer, independent-test tool.
