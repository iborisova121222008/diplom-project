# Locked forest visualization derivation

`backend/scripts/generate_tree_previews.py` reads only the fixed
`results/final_model_gse25055/final_model_package.joblib` package. It validates
the ordered final-probe CSV, 15 feature inputs, 30 fitted sklearn estimators,
and 30 traversable custom roots before writing visualization output.

Each sklearn preview is generated with `sklearn.tree.plot_tree`, truncated at
depth 3. The SVG uses actual probe IDs, RD/pCR labels, thresholds, Gini values,
sample proportions, and class composition from the fitted estimator. The
manifest records full tree depth, node count, used probes, split counts, split
depths, the model-package SHA-256 identity, and generation time.

The generated files are presentation derivatives. The script does not call
`fit`, tune parameters, select thresholds, regenerate canonical predictions,
or change PostgreSQL. A single displayed tree remains one member of the
30-tree ensemble and is not presented as the forest's complete decision.
