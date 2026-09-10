import numpy as np



class TreeNode:
    """Един възел от дървото."""

    def __init__(
        self,
        probability,
        prediction,
        feature_index=None,
        threshold=None,
        left=None,
        right=None
    ):
        self.probability = probability
        self.prediction = prediction
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right

    def is_leaf(self):
        """Връща True, когато възелът няма деца."""

        return self.left is None and self.right is None


def calculate_class_weights(y):
    """
    Изчислява balanced тегло за всеки клас.

    По-рядко срещаният клас получава по-голямо тегло.
    Формулата е същата като при class_weight="balanced":

        брой пациенти / (брой класове * брой пациенти от класа)
    """

    if len(y) == 0:
        raise ValueError(
            "Cannot calculate class weights from an empty group."
        )

    classes, counts = np.unique(
        y,
        return_counts=True
    )

    number_of_samples = len(y)
    number_of_classes = len(classes)
    class_weights = {}

    for class_value, class_count in zip(
        classes,
        counts
    ):
        class_weights[class_value] = (
            number_of_samples
            / (number_of_classes * class_count)
        )

    return class_weights


def calculate_total_weight(
    y,
    class_weights=None
):
    """Връща общото тегло на пациентите в една група."""

    if class_weights is None:
        return float(len(y))

    total_weight = 0.0

    for class_value in y:
        total_weight += class_weights.get(
            class_value,
            1.0
        )

    return total_weight


def gini_impurity(
    y,
    class_weights=None
):
    """
    Изчислява Gini impurity за една група пациенти.

    Без class_weights всички пациенти имат еднаква тежест.
    При class_weights редкият клас участва с по-голяма тежест.
    """

    if len(y) == 0:
        return 0.0

    total_weight = calculate_total_weight(
        y,
        class_weights
    )

    if total_weight == 0.0:
        return 0.0

    gini = 1.0
    classes = np.unique(y)

    for class_value in classes:
        class_count = np.sum(
            y == class_value
        )

        if class_weights is None:
            current_class_weight = float(
                class_count
            )
        else:
            current_class_weight = (
                class_count
                * class_weights.get(
                    class_value,
                    1.0
                )
            )

        class_probability = (
            current_class_weight
            / total_weight
        )

        gini = (
            gini
            - class_probability ** 2
        )

    return gini


def test_split(
    X,
    y,
    feature_index,
    threshold
):
    """
    Разделя пациентите по един probe и един праг.

    Ляво:  стойност <= threshold
    Дясно: стойност > threshold
    """

    feature_values = X[
        :,
        feature_index
    ]

    left_mask = (
        feature_values <= threshold
    )

    right_mask = (
        feature_values > threshold
    )

    X_left = X[left_mask]
    y_left = y[left_mask]

    X_right = X[right_mask]
    y_right = y[right_mask]

    return (
        X_left,
        y_left,
        X_right,
        y_right
    )


def gini_index(
    y_left,
    y_right,
    class_weights=None
):
    """Изчислява общия Gini индекс на едно разделяне."""

    left_weight = calculate_total_weight(
        y_left,
        class_weights
    )

    right_weight = calculate_total_weight(
        y_right,
        class_weights
    )

    total_weight = (
        left_weight
        + right_weight
    )

    if total_weight == 0.0:
        return 0.0

    left_gini = gini_impurity(
        y_left,
        class_weights
    )

    right_gini = gini_impurity(
        y_right,
        class_weights
    )

    split_gini = (
        (left_weight / total_weight)
        * left_gini
        +
        (right_weight / total_weight)
        * right_gini
    )

    return split_gini


def find_best_split(
    X,
    y,
    feature_indices,
    class_weights=None
):
    """Намира probe-а и прага с най-нисък Gini индекс."""

    best_feature_index = None
    best_threshold = None
    best_gini = float("inf")

    best_X_left = None
    best_y_left = None
    best_X_right = None
    best_y_right = None

    for feature_index in feature_indices:
        feature_values = X[
            :,
            feature_index
        ]

        unique_values = np.unique(
            feature_values
        )

        if len(unique_values) < 2:
            continue

        for value_index in range(
            len(unique_values) - 1
        ):
            lower_value = unique_values[
                value_index
            ]

            upper_value = unique_values[
                value_index + 1
            ]

            threshold = (
                lower_value
                + upper_value
            ) / 2.0

            (
                X_left,
                y_left,
                X_right,
                y_right
            ) = test_split(
                X,
                y,
                feature_index,
                threshold
            )

            if len(y_left) == 0:
                continue

            if len(y_right) == 0:
                continue

            current_gini = gini_index(
                y_left,
                y_right,
                class_weights
            )

            if current_gini < best_gini:
                best_feature_index = feature_index
                best_threshold = threshold
                best_gini = current_gini

                best_X_left = X_left
                best_y_left = y_left
                best_X_right = X_right
                best_y_right = y_right

    return {
        "feature_index": best_feature_index,
        "threshold": best_threshold,
        "gini": best_gini,
        "X_left": best_X_left,
        "y_left": best_y_left,
        "X_right": best_X_right,
        "y_right": best_y_right
    }


def create_leaf(
    y,
    class_weights=None
):
    """Създава листо и изчислява вероятността за pCR."""

    if len(y) == 0:
        raise ValueError(
            "Cannot create a leaf from an empty group."
        )

    total_weight = calculate_total_weight(
        y,
        class_weights
    )

    pcr_count = np.sum(
        y == 1
    )

    if class_weights is None:
        pcr_weight = float(
            pcr_count
        )
    else:
        pcr_weight = (
            pcr_count
            * class_weights.get(
                1,
                1.0
            )
        )

    probability = (
        pcr_weight
        / total_weight
    )

    if probability >= 0.5:
        prediction = 1
    else:
        prediction = 0

    return TreeNode(
        probability=probability,
        prediction=prediction
    )


def should_stop(
    y,
    current_depth,
    max_depth,
    min_samples_split,
    class_weights=None
):
    """Проверява дали текущият възел трябва да стане листо."""

    if len(y) == 0:
        return True

    if gini_impurity(
        y,
        class_weights
    ) == 0.0:
        return True

    if current_depth >= max_depth:
        return True

    if len(y) < min_samples_split:
        return True

    return False


def select_random_features(
    number_of_features,
    max_features,
    random_generator
):
    """Избира случайна част от probes за текущия възел."""

    all_feature_indices = np.arange(
        number_of_features
    )

    if max_features is None:
        return all_feature_indices.tolist()

    if max_features < 1:
        raise ValueError(
            "max_features must be at least 1."
        )

    if max_features >= number_of_features:
        return all_feature_indices.tolist()

    selected_indices = random_generator.choice(
        all_feature_indices,
        size=max_features,
        replace=False
    )

    return selected_indices.tolist()


def build_tree(
    X,
    y,
    max_depth,
    min_samples_split,
    current_depth=0,
    max_features=None,
    random_generator=None,
    class_weights=None
):
    """Построява Decision Tree чрез рекурсивно разделяне."""

    if random_generator is None:
        random_generator = np.random.RandomState(
            42
        )

    if should_stop(
        y,
        current_depth,
        max_depth,
        min_samples_split,
        class_weights
    ):
        return create_leaf(
            y,
            class_weights
        )

    number_of_features = X.shape[1]

    feature_indices = select_random_features(
        number_of_features,
        max_features,
        random_generator
    )

    best_split = find_best_split(
        X,
        y,
        feature_indices,
        class_weights
    )

    if best_split["feature_index"] is None:
        return create_leaf(
            y,
            class_weights
        )

    current_gini = gini_impurity(
        y,
        class_weights
    )

    if best_split["gini"] >= current_gini:
        return create_leaf(
            y,
            class_weights
        )

    current_result = create_leaf(
        y,
        class_weights
    )

    node = TreeNode(
        probability=current_result.probability,
        prediction=current_result.prediction,
        feature_index=best_split["feature_index"],
        threshold=best_split["threshold"]
    )

    node.left = build_tree(
        best_split["X_left"],
        best_split["y_left"],
        max_depth,
        min_samples_split,
        current_depth + 1,
        max_features,
        random_generator,
        class_weights
    )

    node.right = build_tree(
        best_split["X_right"],
        best_split["y_right"],
        max_depth,
        min_samples_split,
        current_depth + 1,
        max_features,
        random_generator,
        class_weights
    )

    return node


def predict_one(
    tree,
    patient
):
    """Прави прогноза с едно дърво за един пациент."""

    current_node = tree

    while not current_node.is_leaf():
        feature_value = patient[
            current_node.feature_index
        ]

        if feature_value <= current_node.threshold:
            current_node = current_node.left
        else:
            current_node = current_node.right

    return (
        current_node.prediction,
        current_node.probability
    )


def predict_tree(
    tree,
    X
):
    """Прави прогнози с едно дърво за всички пациенти."""

    predictions = []
    probabilities = []

    for patient_index in range(
        len(X)
    ):
        patient = X[
            patient_index
        ]

        prediction, probability = predict_one(
            tree,
            patient
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
