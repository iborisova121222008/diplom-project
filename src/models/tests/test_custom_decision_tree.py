import numpy as np

from src.models.custom_decision_tree import (
    TreeNode,
    gini_impurity,
    test_split as split_data,
    gini_index,
    find_best_split,
    create_leaf,
    should_stop,
    select_random_features,
    build_tree,
    predict_one,
    predict_tree,
    calculate_class_weights
)


# Общи примерни данни.
#
# Редовете са пациенти.
# Колоните са характеристики, например probes.
X_TEST = np.array([
    [2.1, 10.0],
    [2.8, 11.0],
    [6.5, 20.0],
    [7.2, 21.0]
])


# Реалните класове на пациентите.
#
# 0 = RD
# 1 = pCR
Y_TEST = np.array([
    0,
    0,
    1,
    1
])


def test_balanced_class_weights():

    y = np.array([
        0,
        0,
        0,
        0,
        1
    ])

    class_weights = calculate_class_weights(y)

    assert np.isclose(
        class_weights[0],
        0.625
    )

    assert np.isclose(
        class_weights[1],
        2.5
    )


def test_weighted_gini_impurity():

    y = np.array([
        0,
        0,
        0,
        0,
        1
    ])

    class_weights = calculate_class_weights(y)

    weighted_gini = gini_impurity(
        y,
        class_weights
    )

    assert np.isclose(
        weighted_gini,
        0.5
    )


def test_weighted_leaf_probability():

    y = np.array([
        0,
        0,
        0,
        0,
        1
    ])

    class_weights = calculate_class_weights(y)

    leaf = create_leaf(
        y,
        class_weights
    )

    assert np.isclose(
        leaf.probability,
        0.5
    )

    assert leaf.prediction == 1


def test_tree_node_is_leaf():
    """
    Проверява дали TreeNode правилно разпознава листо.
    """

    leaf = TreeNode(
        probability=0.80,
        prediction=1
    )

    assert leaf.is_leaf() is True
    assert leaf.probability == 0.80
    assert leaf.prediction == 1


def test_gini_impurity():
    """
    Проверява Gini impurity за три различни групи.
    """

    pure_group = np.array([
        0,
        0,
        0,
        0
    ])

    mixed_group = np.array([
        0,
        0,
        1,
        1
    ])

    mostly_rd_group = np.array([
        0,
        0,
        0,
        1
    ])

    assert np.isclose(
        gini_impurity(pure_group),
        0.0
    )

    assert np.isclose(
        gini_impurity(mixed_group),
        0.5
    )

    assert np.isclose(
        gini_impurity(mostly_rd_group),
        0.375
    )


def test_data_split():
    """
    Проверява разделянето на пациентите
    по характеристика 0 и праг 4.0.
    """

    X_left, y_left, X_right, y_right = split_data(
        X_TEST,
        Y_TEST,
        feature_index=0,
        threshold=4.0
    )

    expected_y_left = np.array([
        0,
        0
    ])

    expected_y_right = np.array([
        1,
        1
    ])

    assert len(X_left) == 2
    assert len(X_right) == 2

    assert np.array_equal(
        y_left,
        expected_y_left
    )

    assert np.array_equal(
        y_right,
        expected_y_right
    )


def test_complete_split_gini():
    """
    Проверява качеството на цялото разделяне.

    Лявата група съдържа само RD,
    а дясната група съдържа само pCR.
    Следователно разделянето е напълно чисто.
    """

    y_left = np.array([
        0,
        0
    ])

    y_right = np.array([
        1,
        1
    ])

    result = gini_index(
        y_left,
        y_right
    )

    assert np.isclose(
        result,
        0.0
    )


def test_find_best_split():
    """
    Проверява дали алгоритъмът намира
    най-доброто разделяне на примерните данни.
    """

    feature_indices = np.array([
        0,
        1
    ])

    best_split = find_best_split(
        X_TEST,
        Y_TEST,
        feature_indices
    )

    assert best_split["feature_index"] == 0

    assert np.isclose(
        best_split["threshold"],
        4.65
    )

    assert np.isclose(
        best_split["gini"],
        0.0
    )


def test_create_rd_leaf():
    """
    Проверява създаването на листо,
    в което преобладава клас RD.
    """

    y = np.array([
        0,
        0,
        1
    ])

    leaf = create_leaf(y)

    assert leaf.is_leaf() is True
    assert leaf.prediction == 0

    assert np.isclose(
        leaf.probability,
        1.0 / 3.0
    )


def test_create_pcr_leaf():
    """
    Проверява създаването на листо,
    в което преобладава клас pCR.
    """

    y = np.array([
        0,
        1,
        1
    ])

    leaf = create_leaf(y)

    assert leaf.is_leaf() is True
    assert leaf.prediction == 1

    assert np.isclose(
        leaf.probability,
        2.0 / 3.0
    )


def test_should_stop_for_pure_group():
    """
    Чиста група не трябва да се разделя повече.
    """

    y = np.array([
        0,
        0,
        0
    ])

    result = should_stop(
        y,
        current_depth=0,
        max_depth=5,
        min_samples_split=2
    )

    assert result is True


def test_should_continue_for_mixed_group():
    """
    Смесена и достатъчно голяма група
    трябва да продължи да се разделя.
    """

    y = np.array([
        0,
        0,
        1,
        1
    ])

    result = should_stop(
        y,
        current_depth=0,
        max_depth=5,
        min_samples_split=2
    )

    assert result is False


def test_select_random_features():
    """
    Проверява дали се избират точният брой
    характеристики без повторение.
    """

    random_generator = np.random.RandomState(
        42
    )

    selected_features = select_random_features(
        number_of_features=10,
        max_features=3,
        random_generator=random_generator
    )

    assert len(selected_features) == 3

    assert len(
        np.unique(selected_features)
    ) == 3


def test_build_tree():
    """
    Проверява построяването на просто дърво.
    """

    tree = build_tree(
        X_TEST,
        Y_TEST,
        max_depth=3,
        min_samples_split=2,
        max_features=2
    )

    assert tree.is_leaf() is False
    assert tree.feature_index == 0

    assert np.isclose(
        tree.threshold,
        4.65
    )

    assert tree.left.is_leaf() is True
    assert tree.right.is_leaf() is True

    assert tree.left.prediction == 0
    assert tree.right.prediction == 1


def test_predict_one_patient():
    """
    Проверява прогнозата за един пациент.
    """

    tree = build_tree(
        X_TEST,
        Y_TEST,
        max_depth=3,
        min_samples_split=2,
        max_features=2
    )

    prediction, probability = predict_one(
        tree,
        X_TEST[0]
    )

    assert prediction == 0

    assert np.isclose(
        probability,
        0.0
    )


def test_predict_multiple_patients():
    """
    Проверява прогнозите за всички пациенти.
    """

    tree = build_tree(
        X_TEST,
        Y_TEST,
        max_depth=3,
        min_samples_split=2,
        max_features=2
    )

    predictions, probabilities = predict_tree(
        tree,
        X_TEST
    )

    assert np.array_equal(
        predictions,
        Y_TEST
    )

    assert len(probabilities) == len(Y_TEST)

    assert np.all(
        probabilities >= 0.0
    )

    assert np.all(
        probabilities <= 1.0
    )
