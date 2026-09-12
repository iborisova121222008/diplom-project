import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.auth import verify_password
from app.database import SessionLocal
from app.main import app
from app.models import User
from app.schemas import (
    PASSWORD_VALIDATION_MESSAGE,
    RESEARCHER_ID_VALIDATION_MESSAGE,
)


client = TestClient(app)
anonymous_client = TestClient(app)
AUTH_RESEARCHER_ID = "phase4_researcher"
AUTH_PASSWORD = "Secure-Test1!"


@pytest.fixture(scope="module", autouse=True)
def authenticated_client():
    registration = client.post(
        "/api/auth/register",
        json={"researcher_id": AUTH_RESEARCHER_ID, "password": AUTH_PASSWORD},
    )
    assert registration.status_code == 201
    client.headers["Authorization"] = (
        f"Bearer {registration.json()['access_token']}"
    )
    yield
    client.headers.pop("Authorization", None)


def test_valid_researcher_id_registers_once_hashes_password_and_authenticates():
    plain_password = "Another-Secure2!"
    response = client.post(
        "/api/auth/register",
        json={
            "researcher_id": " Valid.Researcher_01 ",
            "password": plain_password,
        },
    )
    assert response.status_code == 201
    assert set(response.json()) == {
        "access_token", "token_type", "researcher_id"
    }
    assert response.json()["researcher_id"] == "valid.researcher_01"

    with SessionLocal() as session:
        user = session.scalar(
            select(User).where(User.researcher_id == "valid.researcher_01")
        )
        assert user is not None
        assert user.password_hash != plain_password
        assert user.password_hash.startswith("$argon2")
        assert verify_password(plain_password, user.password_hash)

    protected = anonymous_client.get(
        "/api/datasets",
        headers={
            "Authorization": f"Bearer {response.json()['access_token']}"
        },
    )
    assert protected.status_code == 200


def test_duplicate_registration_has_clear_bulgarian_error():
    response = client.post(
        "/api/auth/register",
        json={"researcher_id": AUTH_RESEARCHER_ID, "password": AUTH_PASSWORD},
    )
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Този Researcher ID вече е регистриран."
    }


def test_case_insensitive_duplicate_researcher_id_is_rejected():
    first = client.post(
        "/api/auth/register",
        json={"researcher_id": "Case.Researcher", "password": AUTH_PASSWORD},
    )
    duplicate = client.post(
        "/api/auth/register",
        json={"researcher_id": "CASE.RESEARCHER", "password": AUTH_PASSWORD},
    )
    assert first.status_code == 201
    assert first.json()["researcher_id"] == "case.researcher"
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Този Researcher ID вече е регистриран."
    with SessionLocal() as session:
        count = session.scalar(
            select(func.count()).select_from(User).where(
                func.lower(User.researcher_id) == "case.researcher"
            )
        )
        assert count == 1


@pytest.mark.parametrize(
    "researcher_id",
    ("ab", "researcher id", "researcher@id"),
)
def test_invalid_researcher_id_has_concise_bulgarian_error(researcher_id):
    response = client.post(
        "/api/auth/register",
        json={"researcher_id": researcher_id, "password": AUTH_PASSWORD},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": RESEARCHER_ID_VALIDATION_MESSAGE}


@pytest.mark.parametrize(
    "password",
    (
        "secure-test1!",
        "SECURE-TEST1!",
        "Secure-Test!",
        "SecureTest1",
        "S1!aaaa",
        " Secure-Test1!",
    ),
)
def test_invalid_registration_password_has_one_bulgarian_error(password):
    response = client.post(
        "/api/auth/register",
        json={"researcher_id": "password_test", "password": password},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": PASSWORD_VALIDATION_MESSAGE}


def test_successful_login_response_schema():
    response = client.post(
        "/api/auth/login",
        json={
            "researcher_id": f"  {AUTH_RESEARCHER_ID.upper()}  ",
            "password": AUTH_PASSWORD,
        },
    )
    assert response.status_code == 200
    assert set(response.json()) == {
        "access_token", "token_type", "researcher_id"
    }
    assert response.json()["token_type"] == "bearer"
    assert response.json()["researcher_id"] == AUTH_RESEARCHER_ID


def test_invalid_login_uses_generic_bulgarian_error():
    response = client.post(
        "/api/auth/login",
        json={"researcher_id": AUTH_RESEARCHER_ID, "password": "Wrong-Test9!"},
    )
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Невалиден Researcher ID или парола."
    }


def test_missing_and_invalid_jwt_are_rejected():
    missing = anonymous_client.get("/api/datasets")
    invalid = anonymous_client.get(
        "/api/datasets",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert invalid.headers["www-authenticate"] == "Bearer"


def test_authenticated_scientific_response_values_are_unchanged():
    response = client.get("/api/datasets")
    assert response.status_code == 200
    counts = {
        item["accession"]: item["included_patient_count"]
        for item in response.json()
    }
    assert counts == {"GSE25055": 306, "GSE25065": 182}


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


def test_expression_preview_is_bounded_and_uses_allowlisted_datasets():
    response = client.get(
        "/api/expression-preview",
        params={
            "dataset": "GSE25055", "patient_search": "GSM61509",
            "probe_search": "1007", "row_limit": 3, "column_limit": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["dataset"] == "GSE25055"
    assert len(body["patients"]) <= 3
    assert body["probes"][0] == "1007_s_at"
    assert len(body["probes"]) <= 2
    assert all(len(row) == len(body["probes"]) for row in body["values"])
    assert client.get(
        "/api/expression-preview", params={"dataset": "../../secret"}
    ).status_code == 422
    assert client.get(
        "/api/expression-preview", params={"row_limit": 21}
    ).status_code == 422


def test_expression_window_exports_only_the_requested_window():
    csv_response = client.get(
        "/api/expression-preview/export",
        params={"dataset": "GSE25065", "row_limit": 2, "column_limit": 3},
    )
    assert csv_response.status_code == 200
    assert len(csv_response.text.strip().splitlines()) == 3
    xlsx_response = client.get(
        "/api/expression-preview/export",
        params={"dataset": "GSE25065", "row_limit": 2, "column_limit": 3, "format": "xlsx"},
    )
    assert xlsx_response.status_code == 200
    assert xlsx_response.content.startswith(b"PK")


def test_forest_structure_distinguishes_custom_and_sklearn_models():
    custom = client.get(
        "/api/forest/structure",
        params={"implementation": "custom", "tree_index": 1, "visible_depth": 2},
    )
    sklearn = client.get(
        "/api/forest/structure",
        params={"implementation": "sklearn", "tree_index": 1, "visible_depth": 2},
    )
    assert custom.status_code == sklearn.status_code == 200
    assert custom.json()["implementation"] == "custom"
    assert sklearn.json()["implementation"] == "sklearn"
    assert custom.json()["nodes"][0]["probe_id"] is not None
    assert all(item["depth"] <= 2 for item in custom.json()["nodes"])


def test_prediction_filters_and_summaries_use_persisted_rows():
    response = client.get(
        "/api/predictions",
        params={
            "experiment": "balanced-rf-nested-cv",
            "model": "custom_random_forest", "correct": "false",
            "sort_by": "patient_id", "sort_order": "asc", "limit": 10,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] == 0
    assert body["incorrect"] == body["total"]
    assert all(item["actual_class"] != item["predicted_class"] for item in body["items"])


def test_metrics_exports_do_not_expose_classification_cutoffs():
    response = client.get(
        "/api/table-exports/metrics",
        params={"cohort": "external", "model": "comparison"},
    )
    assert response.status_code == 200
    assert "roc_auc" in response.text
    assert "threshold" not in response.text.lower()

    features = client.get(
        "/api/table-exports/feature-stability",
        params={"minimum_frequency": 8, "final_only": "true"},
    )
    assert features.status_code == 200
    assert "selection_frequency" in features.text
    assert all(
        float(line.split(",")[3]) >= 0.8
        for line in features.text.strip().splitlines()[1:]
    )


def test_openapi_application_routes_are_get_only():
    schema = client.get("/openapi.json").json()
    for path, methods in schema["paths"].items():
        if not path.startswith("/api/"):
            continue
        allowed = {"post", "parameters"} if path in {
            "/api/auth/register", "/api/auth/login"
        } else {"get", "parameters"}
        assert set(methods).issubset(allowed), path


@pytest.mark.parametrize(
    "origin", ("http://localhost:5173", "http://127.0.0.1:5173")
)
@pytest.mark.parametrize("path", ("/api/auth/register", "/api/auth/login"))
def test_authentication_preflight_allows_exact_development_origins(origin, path):
    response = anonymous_client.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "POST" in response.headers["access-control-allow-methods"]
    assert response.headers.get("access-control-allow-credentials") != "true"


@pytest.mark.parametrize(
    ("origin", "researcher_id"),
    (
        ("http://localhost:5173", "cors_localhost"),
        ("http://127.0.0.1:5173", "cors_loopback"),
    ),
)
def test_registration_and_login_allow_both_development_origins(
    origin,
    researcher_id,
):
    headers = {"Origin": origin}
    registration = anonymous_client.post(
        "/api/auth/register",
        json={"researcher_id": researcher_id, "password": AUTH_PASSWORD},
        headers=headers,
    )
    assert registration.status_code == 201
    assert registration.headers["access-control-allow-origin"] == origin

    login = anonymous_client.post(
        "/api/auth/login",
        json={"researcher_id": researcher_id, "password": AUTH_PASSWORD},
        headers=headers,
    )
    assert login.status_code == 200
    assert login.headers["access-control-allow-origin"] == origin
    assert login.json()["researcher_id"] == researcher_id


@pytest.mark.parametrize(("path", "params"), [
    ("/api/health", {}),
    ("/api/datasets", {}),
    ("/api/expression-preview", {}),
    ("/api/preprocessing", {}),
    ("/api/features", {}),
    ("/api/models", {}),
    ("/api/cv-results", {}),
    ("/api/comparison", {}),
    ("/api/final-validation", {}),
    ("/api/experiments", {}),
    ("/api/predictions", {"experiment": "balanced-rf-nested-cv"}),
    ("/api/curves", {"experiment": "balanced-rf-nested-cv"}),
    ("/api/model-disagreements", {}),
    ("/api/fold-feature-similarity", {}),
    ("/api/feature-stability", {}),
    ("/api/feature-heatmap", {}),
    ("/api/feature-frequency-distribution", {}),
    ("/api/forest/manifest", {}),
    ("/api/forest/structure", {}),
    ("/api/forest/trees/1", {}),
    ("/api/reports", {}),
    ("/api/table-exports/metrics", {"cohort": "oof"}),
])
def test_documented_get_routes_return_success(path, params):
    assert client.get(path, params=params).status_code == 200
