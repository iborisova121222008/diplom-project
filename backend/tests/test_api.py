def test_dataset_response_uses_imported_counts(client):
    response = client.get("/api/datasets")

    assert response.status_code == 200
    datasets = {item["accession"]: item for item in response.json()}
    assert datasets["GSE25055"]["included_patient_count"] == 306
    assert datasets["GSE25055"]["excluded_patient_count"] == 4
    assert datasets["GSE25065"]["included_patient_count"] == 182
    assert datasets["GSE25065"]["role"] == "external_validation_only"


def test_cv_response_keeps_result_types_separate(client):
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


def test_comparison_is_explicitly_overall_oof(client):
    response = client.get("/api/comparison")

    assert response.status_code == 200
    assert len(response.json()) == 4
    assert all(
        item["result_type"] == "overall_oof"
        for item in response.json()
    )


def test_feature_context_and_annotation_are_visible(client):
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


def test_final_validation_is_locked_and_external_only(client):
    response = client.get("/api/final-validation")

    assert response.status_code == 200
    body = response.json()
    assert body["dataset"] == "GSE25065"
    assert body["dataset_role"] == "external_validation_only"
    assert body["locked"] is True
    assert body["result_type"] == "locked_external_validation"
    assert len(body["models"]) == 2


def test_no_patient_prediction_endpoint_exists(client):
    assert client.post("/api/predict", json={}).status_code == 404
    assert client.get("/api/predict").status_code == 404


def test_experiments_are_completed_or_locked(client):
    response = client.get("/api/experiments")

    assert response.status_code == 200
    assert len(response.json()) == 5
    assert {item["status"] for item in response.json()} == {
        "completed", "locked"
    }


def test_prediction_records_are_read_only_stored_results(client):
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


def test_curves_use_imported_prediction_records(client):
    response = client.get(
        "/api/curves",
        params={"experiment": "balanced-rf-nested-cv"},
    )

    assert response.status_code == 200
    assert response.json()["result_type"] == "out_of_fold_curves"
    assert len(response.json()["models"]) == 2


def test_fold_similarity_contains_all_pairs(client):
    response = client.get("/api/fold-feature-similarity")

    assert response.status_code == 200
    assert len(response.json()) == 45


def test_external_compatibility_is_exposed_from_dataset_metadata(client):
    response = client.get("/api/datasets")
    external = next(
        item for item in response.json() if item["accession"] == "GSE25065"
    )

    assert external["compatibility_metadata"][
        "probe_order_matches_development"
    ] is True
    assert external["compatibility_metadata"]["missing_final_probes"] == []
