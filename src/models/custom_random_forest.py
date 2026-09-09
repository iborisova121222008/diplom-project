import numpy as np
from src.models.custom_decision_tree import (
    build_tree,
    predict_one
)

def bootstrap_sample(
    X,
    y,
    random_generator
):
    """
    Създава bootstrap извадка
    от обучаващите пациенти.

    Извадката:
    - има същия брой пациенти като X;
    - избира пациентите случайно;
    - позволява един пациент да бъде
      избран повече от веднъж.
    """

    # Намираме броя на пациентите.
    number_of_samples = len(X)

    # Създаваме индексите на пациентите.
    #
    # Например при 4 пациенти:
    # [0, 1, 2, 3]
    patient_indices = np.arange(
        number_of_samples
    )

    # Избираме същия брой индекси,
    # но със заместване.
    #
    # replace=True позволява един пациент
    # да бъде избран повече от веднъж.
    bootstrap_indices = random_generator.choice(
        patient_indices,
        size=number_of_samples,
        replace=True
    )

    # Избираме редовете от X
    # според случайните индекси.
    X_sample = X[
        bootstrap_indices
    ]

    # Избираме съответните класове от y.
    y_sample = y[
        bootstrap_indices
    ]

    return (
        X_sample,
        y_sample,
        bootstrap_indices
    )


"""Стъпка 15 — build_forest() """
def build_forest(
    X,
    y,
    number_of_trees,
    max_depth,
    min_samples_split,
    max_features=None,
    random_state=42
):
    """
    Създава Random Forest от множество
    собствени Decision Trees.

    X:
        Training характеристиките.

    y:
        Реалните training класове.

    number_of_trees:
        Броят дървета в гората.

    max_depth:
        Максималната дълбочина
        на всяко дърво.

    min_samples_split:
        Минималният брой пациенти,
        необходим за разделяне.

    max_features:
        Броят случайни probes,
        проверявани във всеки възел.

    random_state:
        Начална стойност за
        възпроизводим резултат.
    """

    # Random Forest трябва да съдържа
    # поне едно дърво.
    if number_of_trees < 1:
        raise ValueError(
            "number_of_trees must be at least 1."
        )

    # Създаваме генератора,
    # който ще управлява случайността.
    random_generator = np.random.RandomState(
        random_state
    )

    # Ако max_features не е зададено,
    # използваме квадратния корен
    # от общия брой характеристики.
    if max_features is None:
        max_features = int(
            np.sqrt(X.shape[1])
        )

        # Трябва да бъде избрана
        # поне една характеристика.
        if max_features < 1:
            max_features = 1

    # Тук ще събираме
    # всички построени дървета.
    forest = []

    # Създаваме дърветата едно по едно.
    for tree_index in range(
        number_of_trees
    ):
        print(
            "Building tree",
            tree_index + 1,
            "of",
            number_of_trees
        )

        # За всяко дърво създаваме
        # нова bootstrap извадка.
        (
            X_sample,
            y_sample,
            bootstrap_indices
        ) = bootstrap_sample(
            X,
            y,
            random_generator
        )

        # Построяваме едно дърво
        # от текущата bootstrap извадка.
        tree = build_tree(
            X_sample,
            y_sample,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            max_features=max_features,
            random_generator=random_generator
        )

        # Добавяме готовото дърво
        # към гората.
        forest.append(
            tree
        )

    return forest

"""Стъпка 16 — predict_forest_one()"""
def predict_forest_one(
    forest,
    patient
):
    """
    Прави Random Forest прогноза
    за един пациент.

    forest:
        Списък с обучените дървета.

    patient:
        Един ред с probe стойностите
        на пациента.

    Връща:
        prediction  - 0 за RD или 1 за pCR;
        probability - средна вероятност за pCR.
    """

    # Не можем да направим прогноза
    # с празна гора.
    if len(forest) == 0:
        raise ValueError(
            "The forest contains no trees."
        )

    # Тук ще съберем pCR вероятността,
    # дадена от всяко дърво.
    tree_probabilities = []

    # Подаваме пациента
    # на всяко дърво в гората.
    for tree in forest:

        # predict_one връща:
        # - класа на дървото;
        # - вероятността за pCR.
        (
            tree_prediction,
            tree_probability
        ) = predict_one(
            tree,
            patient
        )

        # За общата Random Forest прогноза
        # използваме вероятността.
        tree_probabilities.append(
            tree_probability
        )

    # Изчисляваме средната вероятност
    # от всички дървета.
    forest_probability = np.mean(
        tree_probabilities
    )

    # Превръщаме средната вероятност
    # в краен клас.
    if forest_probability >= 0.5:
        forest_prediction = 1
    else:
        forest_prediction = 0

    return (
        forest_prediction,
        forest_probability
    )


def predict_forest(
    forest,
    X
):
    """
    Прави Random Forest прогнози
    за всички пациенти в X.

    forest:
        Списъкът с обучените дървета.

    X:
        Матрица с пациентите,
        за които правим прогноза.

    Връща:
        predictions   - класовете 0 или 1;
        probabilities - вероятностите за pCR.
    """

    # Не можем да правим прогнози
    # с празна гора.
    if len(forest) == 0:
        raise ValueError(
            "The forest contains no trees."
        )

    # Тук ще събираме крайните класове.
    predictions = []

    # Тук ще събираме средните
    # pCR вероятности.
    probabilities = []

    # Обхождаме пациентите един по един.
    for patient_index in range(
        len(X)
    ):
        # Взимаме един пациент,
        # тоест един ред от X.
        patient = X[
            patient_index
        ]

        # Всички дървета в гората
        # правят прогноза за пациента.
        (
            prediction,
            probability
        ) = predict_forest_one(
            forest,
            patient
        )

        # Запазваме крайния клас.
        predictions.append(
            prediction
        )

        # Запазваме средната
        # вероятност за pCR.
        probabilities.append(
            probability
        )

    # Превръщаме списъците
    # в NumPy масиви.
    predictions = np.array(
        predictions
    )

    probabilities = np.array(
        probabilities
    )

    return predictions, probabilities

if __name__ == "__main__":

    """Тест 13 степ на bootstrap_sample()"""

    print("Testing bootstrap_sample:")

    X_test = np.array([
        [2.1, 10.0],
        [2.8, 11.0],
        [6.5, 20.0],
        [7.2, 21.0]
    ])

    y_test = np.array([
        0,
        0,
        1,
        1
    ])

    random_generator = np.random.RandomState(
        42
    )

    (
        X_sample,
        y_sample,
        bootstrap_indices
    ) = bootstrap_sample(
        X_test,
        y_test,
        random_generator
    )

    print(
        "Original patient indices:",
        np.arange(len(X_test))
    )

    print(
        "Bootstrap indices:",
        bootstrap_indices
    )

    print(
        "Bootstrap X:"
    )

    print(
        X_sample
    )

    print(
        "Bootstrap y:",
        y_sample
    )

    print(
        " in the original dataset:",
        len(X_test)
    )

    print(
        "Patients in the bootstrap sample:",
        len(X_sample)
    )



    """TEST Стъпка 15 — build_forest() """

    print("\nTesting build_forest:")

    forest = build_forest(
        X_test,
        y_test,
        number_of_trees=5,
        max_depth=3,
        min_samples_split=2,
        max_features=1,
        random_state=42
    )

    print(
        "\nNumber of trees:",
        len(forest)
    )

    # Разглеждаме корена
    # на всяко построено дърво.
    for tree_index in range(
        len(forest)
    ):
        tree = forest[
            tree_index
        ]

        print(
            "Tree",
            tree_index + 1,
            "| Root is leaf:",
            tree.is_leaf(),
            "| Feature:",
            tree.feature_index,
            "| Threshold:",
            tree.threshold
        )


        """TEST Стъпка 16 — predict_forest_one()"""

    print(
        "\nTesting predict_forest_one:"
    )

    # Взимаме първия пациент.
    first_patient = X_test[0]

    # Получаваме общата прогноза
    # от всички дървета.
    (
        forest_prediction,
        forest_probability
    ) = predict_forest_one(
        forest,
        first_patient
    )

    print(
        "Actual class:",
        y_test[0]
    )

    print(
        "Forest prediction:",
        forest_prediction
    )

    print(
        "Forest pCR probability:",
        forest_probability
    )

    print(
        "Probability is valid:",
        0.0 <= forest_probability <= 1.0
    )


    """TEST Стъпка 17 — predict_forest()"""

    print(
        "\nIndividual tree results:"
    )

    for tree_index in range(
        len(forest)
    ):
        (
            tree_prediction,
            tree_probability
        ) = predict_one(
            forest[tree_index],
            first_patient
        )

        print(
            "Tree",
            tree_index + 1,
            "| Prediction:",
            tree_prediction,
            "| pCR probability:",
            tree_probability
        )


        print(
        "\nTesting predict_forest:"
    )

    (
        forest_predictions,
        forest_probabilities
    ) = predict_forest(
        forest,
        X_test
    )

    print(
        "Actual classes:",
        y_test
    )

    print(
        "Forest predictions:",
        forest_predictions
    )

    print(
        "Forest pCR probabilities:",
        forest_probabilities
    )

    # Проверяваме броя на прогнозите.
    print(
        "Number of predictions:",
        len(forest_predictions)
    )

    # Проверяваме дали всички вероятности
    # са между 0 и 1.
    probabilities_are_valid = np.all(
        (
            forest_probabilities >= 0.0
        )
        &
        (
            forest_probabilities <= 1.0
        )
    )

    print(
        "All probabilities are valid:",
        probabilities_are_valid
    )

    # Изчисляваме примерна accuracy.
    correct_predictions = np.sum(
        forest_predictions == y_test
    )

    accuracy = (
        correct_predictions / len(y_test)
    )

    print(
        "Forest accuracy:",
        accuracy
    )