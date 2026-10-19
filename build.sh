#!/usr/bin/env sh
# Rebuild docs/index.html from the three report files. Run from the repository root.
python scripts/build_gallery.py \
  --dataset docs/reports/02_dataset_report.html \
  --training docs/reports/03_training_validation.html \
  --independent docs/reports/05_independent_test_report.html \
  --map docs/img/susceptibility_map.png \
  --map-caption "Susceptibility classes from RF and XGBoost. The river channel falls in the lowest class because permanent water was not excluded from the training table in this run." \
  --about docs/about_example.txt --out docs
