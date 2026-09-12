from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dataset_response_uses_imported_counts():
    response = client.get("/api/datasets")

    assert response.status_code == 200
    datasets = {item["accession"]: item for item in response.json()}
    assert datasets["GSE25055"]["included_patient_count"] == 306
    assert datasets["GSE25055"]["excluded_patient_count"] == 4
    assert datasets["GSE25065"]["included_patient_count"] == 182
    assert datasets["GSE25065"]["role"] == "external_validation_only"


def test_cv_response_keeps_result_types_separate():
    response = client.get("/api/cv-results")

    assert response.status_code == 200
    records = response.json()
    assert len(records) == 4
    assert all(len(item["folds"]) == 10 for item in records)
    assert all(
        item["summary"]["result_type"] ==
        "fold_mean_and_sample_standard_deviation"
        for item in records
    )


def test_comparison_is_explicitly_overall_oof():
    response = client.get("/api/comparison")

    assert response.status_code == 200
    assert len(response.json()) == 4
    assert all(
        item["result_type"] == "overall_oof"
        for item in response.json()
    )


def test_feature_context_and_annotation_are_visible():
    response = client.get(
        "/api/features",
        params={"search": "HMGXB3", "limit": 10}
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["probe_id"] == "212431_at"
    assert item["experiment_slug"] == "lasso-logistic-nested-cv"
    assert item["annotation"]["gene_symbol"] == "HMGXB3"
    assert item["annotation"]["display_only"] is True


def test_final_validation_is_locked_and_external_only():
    response = client.get("/api/final-validation")

    assert response.status_code == 200
    body = response.json()
    assert body["dataset"] == "GSE25065"
    assert body["dataset_role"] == "external_validation_only"
    assert body["locked"] is True
    assert body["result_type"] == "locked_external_validation"
    assert len(body["models"]) == 2


def test_no_patient_prediction_endpoint_exists():
    assert client.post("/api/predict", json={}).status_code == 404
    assert client.get("/api/predict").status_code == 404


def test_experiments_are_completed_or_locked():
    response = client.get("/api/experiments")

    assert response.status_code == 200
    assert len(response.json()) == 5
    assert {item["status"] for item in response.json()} == {
        "completed", "locked"
    }


def test_prediction_records_are_read_only_stored_results():
    response = client.get(
        "/api/predictions",
        params={
            "experiment": "locked-external-validation-gse25065",
            "model": "custom_random_forest",
            "limit": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 182
    assert len(response.json()["items"]) == 5


def test_curves_use_imported_prediction_records():
    response = client.get(
        "/api/curves",
        params={"experiment": "balanced-rf-nested-cv"},
    )

    assert response.status_code == 200
    assert response.json()["result_type"] == "out_of_fold_curves"
    assert len(response.json()["models"]) == 2


def test_fold_similarity_contains_all_pairs():
    response = client.get("/api/fold-feature-similarity")

    assert response.status_code == 200
    assert len(response.json()) == 45


def test_feature_frequency_distribution_covers_distinct_root_lasso_probes():
    response = client.get("/api/feature-frequency-distribution")
    assert response.status_code == 200
    assert len(response.json()) == 10
    assert sum(item["probe_count"] for item in response.json()) == 2015


def test_external_compatibility_is_exposed_from_dataset_metadata():
    response = client.get("/api/datasets")
    external = next(
        item for item in response.json() if item["accession"] == "GSE25065"
    )

    assert external["compatibility_metadata"][
        "probe_order_matches_development"
    ] is True
    assert external["compatibility_metadata"]["missing_final_probes"] == []


def test_locked_forest_manifest_and_tree_assets_are_read_only():
    manifest_response = client.get("/api/forest/manifest")
    assert manifest_response.status_code == 200
    manifest = manifest_response.json()
    assert manifest["tree_count"] == 30
    assert manifest["custom_tree_count"] == 30
    assert len(manifest["trees"]) == 30
    assert len(manifest["selected_probes"]) == 15
    assert all(
        probe in manifest["selected_probes"]
        for tree in manifest["trees"]
        for probe in tree["used_probes"]
    )

    tree_response = client.get("/api/forest/trees/1")
    assert tree_response.status_code == 200
    assert tree_response.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in tree_response.text
    assert client.get("/api/forest/trees/31").status_code == 404


def test_filtered_table_exports_preserve_filters_and_support_xlsx():
    csv_response = client.get(
        "/api/table-exports/fold-results",
        params={"model": "custom_random_forest", "fold": 3},
    )
    assert csv_response.status_code == 200
    assert "custom_random_forest" in csv_response.text
    assert "sklearn_random_forest" not in csv_response.text
    assert "model" in csv_response.headers["x-export-filters"]

    xlsx_response = client.get(
        "/api/table-exports/features",
        params={"experiment": "final-model-gse25055", "format": "xlsx"},
    )
    assert xlsx_response.status_code == 200
    assert xlsx_response.content.startswith(b"PK")
