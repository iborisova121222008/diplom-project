import numpy as np

from src.models.custom_random_forest import (
    bootstrap_sample,
    build_forest,
    predict_forest_one,
    predict_forest
)


# Малък примерен набор от данни.
#
# Всеки ред е пациент.
# Всяка колона е характеристика.
X_TEST = np.array([
    [2.1, 10.0],
    [2.8, 11.0],
    [6.5, 20.0],
    [7.2, 21.0]
])


# Реалните класове:
#
# 0 = RD
# 1 = pCR
Y_TEST = np.array([
    0,
    0,
    1,
    1
])


def test_bootstrap_sample_size():
    """
    Проверява дали bootstrap извадката
    съдържа същия брой пациенти като
    първоначалния обучаващ набор.
    """

    random_generator = np.random.RandomState(
        42
    )

    X_sample, y_sample, bootstrap_indices = bootstrap_sample(
        X_TEST,
        Y_TEST,
        random_generator
    )

    assert len(X_sample) == len(X_TEST)
    assert len(y_sample) == len(Y_TEST)
    assert len(bootstrap_indices) == len(X_TEST)


def test_bootstrap_sample_alignment():
    """
    Проверява дали X и y остават правилно свързани.

    Ако бъде избран пациент с индекс 2,
    трябва да се вземат едновременно:
    X_TEST[2] и Y_TEST[2].
    """

    random_generator = np.random.RandomState(
        42
    )

    X_sample, y_sample, bootstrap_indices = bootstrap_sample(
        X_TEST,
        Y_TEST,
        random_generator
    )

    expected_X = X_TEST[
        bootstrap_indices
    ]

    expected_y = Y_TEST[
        bootstrap_indices
    ]

    assert np.array_equal(
        X_sample,
        expected_X
    )

    assert np.array_equal(
        y_sample,
        expected_y
    )


def test_build_forest_number_of_trees():
    """
    Проверява дали гората съдържа
    зададения брой дървета.
    """

    forest = build_forest(
        X_TEST,
        Y_TEST,
        number_of_trees=5,
        max_depth=3,
        min_samples_split=2,
        max_features=2,
        random_state=42
    )

    assert len(forest) == 5


def test_predict_forest_one():
    """
    Проверява прогнозата на цялата гора
    за един пациент.
    """

    forest = build_forest(
        X_TEST,
        Y_TEST,
        number_of_trees=5,
        max_depth=3,
        min_samples_split=2,
        max_features=2,
        random_state=42
    )

    prediction, probability = predict_forest_one(
        forest,
        X_TEST[0]
    )

    # Прогнозата трябва да бъде един
    # от двата допустими класа.
    assert prediction in [
        0,
        1
    ]

    # Вероятността трябва да бъде
    # между 0 и 1.
    assert probability >= 0.0
    assert probability <= 1.0


def test_predict_forest_multiple_patients():
    """
    Проверява прогнозите на гората
    за всички пациенти.
    """

    forest = build_forest(
        X_TEST,
        Y_TEST,
        number_of_trees=5,
        max_depth=3,
        min_samples_split=2,
        max_features=2,
        random_state=42
    )

    predictions, probabilities = predict_forest(
        forest,
        X_TEST
    )

    assert len(predictions) == len(Y_TEST)
    assert len(probabilities) == len(Y_TEST)

    assert np.all(
        probabilities >= 0.0
    )

    assert np.all(
        probabilities <= 1.0
    )

    assert np.all(
        np.isin(
            predictions,
            [0, 1]
        )
    )


def test_forest_reproducibility():
    """
    Проверява random_state.

    Две гори, обучени с еднакви данни
    и еднакъв random_state, трябва да дадат
    еднакви резултати.
    """

    first_forest = build_forest(
        X_TEST,
        Y_TEST,
        number_of_trees=5,
        max_depth=3,
        min_samples_split=2,
        max_features=2,
        random_state=42
    )

    second_forest = build_forest(
        X_TEST,
        Y_TEST,
        number_of_trees=5,
        max_depth=3,
        min_samples_split=2,
        max_features=2,
        random_state=42
    )

    first_predictions, first_probabilities = predict_forest(
        first_forest,
        X_TEST
    )

    second_predictions, second_probabilities = predict_forest(
        second_forest,
        X_TEST
    )

    assert np.array_equal(
        first_predictions,
        second_predictions
    )

    assert np.allclose(
        first_probabilities,
        second_probabilities
    )