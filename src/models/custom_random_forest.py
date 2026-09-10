import numpy as np

from src.models.custom_decision_tree import (
    build_tree,
    calculate_class_weights,
    predict_one
)


def bootstrap_sample(
    X,
    y,
    random_generator
):
    """Създава bootstrap извадка със заместване."""

    number_of_samples = len(X)

    patient_indices = np.arange(
        number_of_samples
    )

    bootstrap_indices = random_generator.choice(
        patient_indices,
        size=number_of_samples,
        replace=True
    )

    X_sample = X[
        bootstrap_indices
    ]

    y_sample = y[
        bootstrap_indices
    ]

    return (
        X_sample,
        y_sample,
        bootstrap_indices
    )


def resolve_class_weights(
    y,
    class_weight
):
    """Преобразува настройката class_weight в речник с тегла."""

    if class_weight is None:
        return None

    if class_weight == "balanced":
        return calculate_class_weights(
            y
        )

    if isinstance(class_weight, dict):
        return class_weight.copy()

    raise ValueError(
        "class_weight must be None, 'balanced', or a dictionary."
    )


def build_forest(
    X,
    y,
    number_of_trees,
    max_depth,
    min_samples_split,
    max_features=None,
    random_state=42,
    class_weight=None
):
    """
    Създава Random Forest от собствени Decision Trees.

    При class_weight="balanced" по-редкият клас получава
    по-голямо тегло при Gini разделянията и в листата.
    """

    if number_of_trees < 1:
        raise ValueError(
            "number_of_trees must be at least 1."
        )

    if len(X) != len(y):
        raise ValueError(
            "X and y must contain the same number of samples."
        )

    if X.shape[1] < 1:
        raise ValueError(
            "X must contain at least one feature."
        )

    random_generator = np.random.RandomState(
        random_state
    )

    class_weights = resolve_class_weights(
        y,
        class_weight
    )

    if max_features is None:
        max_features = int(
            np.sqrt(X.shape[1])
        )

        if max_features < 1:
            max_features = 1

    forest = []

    for tree_index in range(
        number_of_trees
    ):
        print(
            "Building tree",
            tree_index + 1,
            "of",
            number_of_trees
        )

        (
            X_sample,
            y_sample,
            bootstrap_indices
        ) = bootstrap_sample(
            X,
            y,
            random_generator
        )

        tree = build_tree(
            X_sample,
            y_sample,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            max_features=max_features,
            random_generator=random_generator,
            class_weights=class_weights
        )

        forest.append(
            tree
        )

    return forest


def predict_forest_one(
    forest,
    patient,
    classification_threshold=0.5
):
    """Прави Random Forest прогноза за един пациент."""

    if len(forest) == 0:
        raise ValueError(
            "The forest contains no trees."
        )

    if not 0.0 <= classification_threshold <= 1.0:
        raise ValueError(
            "classification_threshold must be between 0 and 1."
        )

    tree_probabilities = []

    for tree in forest:
        tree_prediction, tree_probability = predict_one(
            tree,
            patient
        )

        tree_probabilities.append(
            tree_probability
        )

    forest_probability = float(
        np.mean(tree_probabilities)
    )

    if forest_probability >= classification_threshold:
        forest_prediction = 1
    else:
        forest_prediction = 0

    return (
        forest_prediction,
        forest_probability
    )


def predict_forest(
    forest,
    X,
    classification_threshold=0.5
):
    """Прави Random Forest прогнози за всички пациенти."""

    if len(forest) == 0:
        raise ValueError(
            "The forest contains no trees."
        )

    predictions = []
    probabilities = []

    for patient_index in range(
        len(X)
    ):
        patient = X[
            patient_index
        ]

        prediction, probability = predict_forest_one(
            forest,
            patient,
            classification_threshold
        )

        predictions.append(
            prediction
        )

        probabilities.append(
            probability
        )

    return (
        np.array(predictions),
        np.array(probabilities)
    )
