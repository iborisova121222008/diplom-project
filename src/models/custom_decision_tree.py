import numpy as np
class TreeNode:
    """Един възел от дървото - вътрешен възел разделя пациентите, листо връща готова прогноза."""

    def __init__(self, probability, prediction, feature_index=None, threshold=None, left=None, right=None):
        self.probability = probability      # вероятност за pCR (клас 1)
        self.prediction = prediction        # 0 = RD, 1 = pCR
        self.feature_index = feature_index  # кой probe ползваме за разделяне
        self.threshold = threshold          # прагът за сравнение
        self.left = left                    # ляво поддърво: стойност <= threshold
        self.right = right                  # дясно поддърво: стойност > threshold



    def is_leaf(self):
        """
        Връща True, ако възелът е листо.
        Листото няма ляво и дясно поддърво.
        """
        return self.left is None and self.right is None

    # Създаваме примерно листо.
example_leaf = TreeNode(
    probability=0.80,
    prediction=1
)

"""Продължаваме с първата функция, която реално оценява данните: gini_impurity().

Тя казва на дървото дали дадена група пациенти е „чиста“ или в нея са сме сени RD и pCR."""

def gini_impurity(y):
    """
    Изчислява Gini impurity за група пациенти.

    y съдържа реалните класове:
    0 = RD
    1 = pCR

    По-ниска стойност означава по-чиста група.
    """

    # Празната група няма impurity.
    if len(y) == 0:
        return 0.0

    # Започваме от максимална стойност 1.
    gini = 1.0

    # Намираме различните класове в групата.
    #np.unique(y) извлича уникалните класови етикети, които присъстват в целевата променлива y.
    classes = np.unique(y)   

    # Изчисляваме дела на всеки клас.
    for class_value in classes:

        # Броим колко пациенти са от текущия клас.
        class_count = np.sum(
            y == class_value
        )

        # Изчисляваме каква част от всички пациенти
        # принадлежат към този клас.
        class_probability = (
            class_count / len(y)
        )

        # Изваждаме квадрата на вероятността.
        gini = gini - class_probability ** 2

    return gini

def test_split(X, y, feature_index, threshold):
    """
    Разделя пациентите на лява и дясна група.

    X:
        Матрица с характеристиките.
        Редовете са пациенти.
        Колоните са probes.

    y:
        Реалният клас на всеки пациент:
        0 = RD
        1 = pCR

    feature_index:
        Индексът на probe характеристиката,
        по която се извършва разделянето.

    threshold:
        Праговата стойност за разделянето.
    """

    # Взимаме стойността на избрания probe
    # за всеки пациент.
    feature_values = X[:, feature_index]

    # Получаваме True за пациентите,
    # които трябва да отидат вляво.
    left_mask = feature_values <= threshold

    # Получаваме True за пациентите,
    # които трябва да отидат вдясно.
    right_mask = feature_values > threshold

    # Използваме маските, за да разделим X.
    X_left = X[left_mask]
    X_right = X[right_mask]

    # По същия начин разделяме реалните класове.
    #
    # Това е важно, защото ред 0 в X принадлежи
    # на позиция 0 в y, ред 1 на позиция 1 и т.н.
    y_left = y[left_mask]
    y_right = y[right_mask]

    return X_left, y_left, X_right, y_right


def gini_index(y_left, y_right):
    """
    Изчислява общия Gini индекс
    за лявата и дясната група.

    По-ниска стойност означава
    по-добро разделяне.
    """

    # Намираме общия брой пациенти
    # в двете групи.
    total_size = (
        len(y_left) + len(y_right)
    )

    # Защита срещу деление на нула.
    if total_size == 0:
        return 0.0

    # Изчисляваме Gini impurity
    # поотделно за всяка група.
    left_gini = gini_impurity(y_left)
    right_gini = gini_impurity(y_right)

    # Изчисляваме каква част от всички пациенти
    # се намират в лявата група.
    left_weight = (
        len(y_left) / total_size
    )

    # Изчисляваме каква част от всички пациенти
    # се намират в дясната група.
    right_weight = (
        len(y_right) / total_size
    )

    # Общият Gini индекс е претеглената сума
    # от Gini стойностите на двете групи.
    split_gini = (
        left_weight * left_gini
        +
        right_weight * right_gini
    )

    return split_gini



def find_best_split(X, y, feature_indices):
    """
    Намира най-добрия probe и най-добрия праг
    за разделяне на текущата група пациенти.

    X:
        Матрица с характеристиките.
        Редовете са пациенти.
        Колоните са probes.

    y:
        Реалните класове на пациентите:
        0 = RD
        1 = pCR

    feature_indices:
        Списък с индексите на probes,
        които функцията трябва да провери.
    """

    # Първоначално нямаме намерено разделяне.
    best_feature_index = None
    best_threshold = None

    # Започваме с безкрайно лоша Gini стойност.
    #
    # Всеки реално изчислен Gini индекс
    # ще бъде по-малък от безкрайност.
    best_gini = float("inf")

    # Тук ще запазим групите,
    # получени от най-доброто разделяне.
    best_X_left = None
    best_y_left = None
    best_X_right = None
    best_y_right = None

    # Проверяваме един по един разрешените probes.
    for feature_index in feature_indices:

        # Взимаме стойностите на текущия probe
        # за всички пациенти в текущия възел.
        feature_values = X[:, feature_index]

        # Премахваме повтарящите се стойности
        # и ги подреждаме във възходящ ред.
        unique_values = np.unique(
            feature_values
        )

        # Ако всички пациенти имат еднаква стойност
        # за този probe, той не може да ги раздели.
        if len(unique_values) < 2:
            continue

        # Прагът ще бъде поставен между
        # две съседни различни стойности.
        for value_index in range(
            len(unique_values) - 1
        ):
            lower_value = unique_values[
                value_index
            ]

            upper_value = unique_values[
                value_index + 1
            ]

            # Изчисляваме средата между
            # двете съседни стойности.
            threshold = (
                lower_value + upper_value
            ) / 2.0

            # Изпробваме текущия probe
            # с текущия праг.
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

            # Ако някоя от групите е празна,
            # разделянето не е полезно.
            if len(y_left) == 0:
                continue

            if len(y_right) == 0:
                continue

            # Изчисляваме качеството
            # на текущото разделяне.
            current_gini = gini_index(
                y_left,
                y_right
            )

            # По-нисък Gini означава
            # по-добро разделяне.
            if current_gini < best_gini:
                best_feature_index = feature_index
                best_threshold = threshold
                best_gini = current_gini

                best_X_left = X_left
                best_y_left = y_left
                best_X_right = X_right
                best_y_right = y_right

    # Връщаме всичко необходимо
    # за създаването на възел.
    return {
        "feature_index": best_feature_index,
        "threshold": best_threshold,
        "gini": best_gini,
        "X_left": best_X_left,
        "y_left": best_y_left,
        "X_right": best_X_right,
        "y_right": best_y_right
    }


def create_leaf(y):
  
    # Не можем да създадем листо
    # от празна група пациенти.
    if len(y) == 0:
        raise ValueError(
            "Cannot create a leaf from an empty group."
        )

    # Броим колко пациенти
    # в листото са с pCR.
    pcr_count = np.sum(
        y == 1
    )

    # Вероятността за pCR е делът
    # на pCR пациентите в листото.
    probability = (
        pcr_count / len(y)
    )

    # Ако поне половината пациенти са pCR,
    # листото предсказва клас 1.
    if probability >= 0.5:
        prediction = 1

    # В противен случай листото
    # предсказва клас 0, тоест RD.
    else:
        prediction = 0

    # Създаваме TreeNode без деца.
    #
    # Понеже left и right не са подадени,
    # те автоматично остават None.
    leaf = TreeNode(
        probability=probability,
        prediction=prediction
    )

    return leaf

"""Стъпка 8 — should_stop()- Този параметър предпазва 
дървото от създаване на прекалено малки и специфични групи."""

def should_stop(
    y,
    current_depth,
    max_depth,
    min_samples_split
):
    """
    Проверява дали текущият възел
    трябва да бъде превърнат в листо.

    Връща:
    True  - спираме и създаваме листо;
    False - продължаваме с разделянето.
    """

    # Ако групата е празна,
    # няма какво да разделяме.
    if len(y) == 0:
        return True

    # Ако всички пациенти са от един клас,
    # групата е напълно чиста.
    if gini_impurity(y) == 0.0:
        return True

    # Ако сме достигнали позволената
    # максимална дълбочина, спираме.
    if current_depth >= max_depth:
        return True

    # Ако пациентите са твърде малко,
    # не позволяваме ново разделяне.
    if len(y) < min_samples_split:
        return True

    # Ако никое условие не е изпълнено,
    # дървото може да продължи.
    return False


""" Степ 8 Избира случайна част от характеристиките,
    които ще бъдат проверени в текущия възел."""
def select_random_features(
    number_of_features,
    max_features,
    random_generator
):
    """
    Избира случайна част от характеристиките,
    които ще бъдат проверени в текущия възел.

    number_of_features:
        Общият брой probes.

    max_features:
        Колко probes да бъдат избрани.

    random_generator:
        Генератор за възпроизводим
        случаен избор.
    """

    # Създаваме индексите на всички probes.
    #
    # Например, ако имаме 5 probes:
    # [0, 1, 2, 3, 4]
    all_feature_indices = np.arange(
        number_of_features
    )

    # Ако max_features не е зададено,
    # използваме всички probes.
    #
    # Това запазва поведението
    # на обикновено Decision Tree.
    if max_features is None:
        return all_feature_indices.tolist()

    # Трябва да изберем поне един probe.
    if max_features < 1:
        raise ValueError(
            "max_features must be at least 1."
        )

    # Ако поискаме повече probes,
    # отколкото съществуват,
    # използваме всички налични.
    if max_features >= number_of_features:
        return all_feature_indices.tolist()

    # Избираме случайно max_features probes.
    #
    # replace=False означава:
    # един probe не може да бъде избран
    # повече от веднъж в текущия възел.
    selected_indices = random_generator.choice(
        all_feature_indices,
        size=max_features,
        replace=False
    )

    # Превръщаме NumPy масива
    # в обикновен Python списък.
    selected_indices = (
        selected_indices.tolist()
    )

    return selected_indices

"""Стъпка 9 — build_tree()- Рекурсивно строи дървото."""
def build_tree(
    X,
    y,
    max_depth,
    min_samples_split,
    current_depth=0,
    max_features=None,
    random_generator=None
):
    """
    Построява Decision Tree рекурсивно.

    X:
        Характеристиките на пациентите.

    y:
        Реалните класове:
        0 = RD
        1 = pCR

    max_depth:
        Максималната позволена дълбочина.

    min_samples_split:
        Минималният брой пациенти,
        необходим за ново разделяне.

    current_depth:
        Текущото ниво в дървото.
        Коренът започва от 0.
    """
    # При първото извикване създаваме
    # генератор на случайни числа.
    #
    # При рекурсивните извиквания подаваме
    # същия генератор надолу по дървото.
    if random_generator is None:
        random_generator = np.random.RandomState(
            42
        )

 

    # Стъпка 1:
    # Проверяваме дали трябва да спрем.
    if should_stop(
        y,
        current_depth,
        max_depth,
        min_samples_split
    ):
        return create_leaf(y)

    # Стъпка 2:
    # Намираме броя на характеристиките.
    number_of_features = X.shape[1]

    # Създаваме списък с всички
    # индекси на характеристиките.
    #
    # Ако имаме 3 probes:
    # feature_indices = [0, 1, 2]
    feature_indices = select_random_features(
        number_of_features,
        max_features,
        random_generator
    )

    # Стъпка 3:
    # Намираме най-добрия probe и праг
    # за текущата група пациенти.
    best_split = find_best_split(
        X,
        y,
        feature_indices
    )

    # Ако не е намерено валидно разделяне,
    # превръщаме текущата група в листо.
    if best_split["feature_index"] is None:
        return create_leaf(y)

    # Стъпка 4:
    # Проверяваме дали намереното разделяне
    # действително подобрява чистотата.
    current_gini = gini_impurity(y)

    if best_split["gini"] >= current_gini:
        return create_leaf(y)

    # Стъпка 5:
    # Изчисляваме вероятността и прогнозата
    # на текущия възел.
    current_result = create_leaf(y)

    # Създаваме вътрешен възел.
    node = TreeNode(
        probability=current_result.probability,
        prediction=current_result.prediction,
        feature_index=best_split[
            "feature_index"
        ],
        threshold=best_split[
            "threshold"
        ]
    )

    # Стъпка 6:
    # Строим лявото поддърво.
    #
    # Тук build_tree извиква отново себе си,
    # но само с пациентите от лявата група.
    node.left = build_tree(
        best_split["X_left"],
        best_split["y_left"],
        max_depth,
        min_samples_split,
        current_depth + 1,
        max_features,
        random_generator
    )

    # Стъпка 7:
    # Строим дясното поддърво.
    node.right = build_tree(
        best_split["X_right"],
        best_split["y_right"],
        max_depth,
        min_samples_split,
        current_depth + 1,
        max_features,
        random_generator
    )

    # Връщаме построения възел
    # заедно с двете му поддървета.
    return node


def predict_one(tree, patient):
    """
    Прави прогноза за един пациент.

    tree:
        Коренът на вече обученото дърво.

    patient:
        Един ред с probe стойностите
        на пациента.

    Връща:
        prediction  - 0 за RD или 1 за pCR;
        probability - вероятност за pCR.
    """

    # Започваме обхождането
    # от корена на дървото.
    current_node = tree

    # Продължаваме, докато
    # не достигнем до листо.
    while not current_node.is_leaf():

        # Взимаме стойността на probe-а,
        # записан в текущия възел.
        feature_value = patient[
            current_node.feature_index
        ]

        # Ако стойността е по-малка
        # или равна на прага,
        # преминаваме към лявото дете.
        if feature_value <= current_node.threshold:
            current_node = current_node.left

        # В противен случай
        # преминаваме към дясното дете.
        else:
            current_node = current_node.right

    # Цикълът приключва,
    # когато current_node е листо.
    return (
        current_node.prediction,
        current_node.probability
    )

"""Стъпка 11 — predict_tree()"""
def predict_tree(tree, X):
    """
    Прави прогнози с едно Decision Tree
    за всички пациенти в X.

    tree:
        Коренът на обученото дърво.

    X:
        Матрица с пациенти и характеристики.

    Връща:
        predictions   - прогнози 0 или 1;
        probabilities - вероятности за pCR.
    """

    # Тук ще събираме прогнозите.
    predictions = []

    # Тук ще събираме
    # вероятностите за pCR.
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

        # Прекарваме пациента
        # през дървото.
        (
            prediction,
            probability
        ) = predict_one(
            tree,
            patient
        )

        # Запазваме прогнозата.
        predictions.append(
            prediction
        )

        # Запазваме вероятността.
        probabilities.append(
            probability
        )

    # Превръщаме Python списъците
    # в NumPy масиви.
    predictions = np.array(
        predictions
    )

    probabilities = np.array(
        probabilities
    )

    return predictions, probabilities

"""Тест т. 2 за функцията gini_impurity."""

if __name__ == "__main__":

    # Група само с RD пациенти.
    pure_rd_group = np.array([
        0,
        0,
        0,
        0
    ])

    # Група с еднакъв брой RD и pCR пациенти.
    mixed_group = np.array([
        0,
        0,
        1,
        1
    ])

    # Група с трима RD и един pCR пациент.
    mostly_rd_group = np.array([
        0,
        0,
        0,
        1
    ])

    print(
        "Pure RD group:",
        gini_impurity(pure_rd_group)
    )

    print(
        "Mixed group:",
        gini_impurity(mixed_group)
    )

    print(
        "Mostly RD group:",
        gini_impurity(mostly_rd_group)
    )


    """Тест т. 4 за функцията gini_impurity."""
    print("\nTesting test_split:")

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

    X_left, y_left, X_right, y_right = test_split(
        X_test,
        y_test,
        feature_index=0,
        threshold=4.0
    )

    print("Left X:")
    print(X_left)

    print("Left y:")
    print(y_left)

    print("Right X:")
    print(X_right)

    print("Right y:")
    print(y_right)

        # Изчисляваме Gini индекса
    # на разделянето с праг 4.0.
    good_split_gini = gini_index(
        y_left,
        y_right
    )

    print(
        "\nGini for threshold 4.0:",
        good_split_gini
    )

    """Тест т. 5 за функцията find_best_split."""
    print("\nTesting find_best_split:")

    # Разрешаваме на функцията да провери
    # и двете характеристики.
    feature_indices = [
        0,
        1
    ]

    best_split = find_best_split(
        X_test,
        y_test,
        feature_indices
    )

    print(
        "Best feature index:",
        best_split["feature_index"]
    )

    print(
        "Best threshold:",
        best_split["threshold"]
    )

    print(
        "Best Gini:",
        best_split["gini"]
    )

    print(
        "Left classes:",
        best_split["y_left"]
    )

    print(
        "Right classes:",
        best_split["y_right"]
    )


    """Тест т. 6 за функцията gini_impurity."""

    print("\nTesting create_leaf:")

    # В тази група преобладава RD.
    mostly_rd_classes = np.array([
        0,
        0,
        1
    ])

    rd_leaf = create_leaf(
        mostly_rd_classes
    )

    print(
        "RD leaf probability:",
        rd_leaf.probability
    )

    print(
        "RD leaf prediction:",
        rd_leaf.prediction
    )

    print(
        "RD node is leaf:",
        rd_leaf.is_leaf()
    )


    """Стъпка 7 — create_leaf()"""

    # В тази група преобладава pCR.
    mostly_pcr_classes = np.array([
        0,
        1,
        1
    ])

    pcr_leaf = create_leaf(
        mostly_pcr_classes
    )

    print(
        "\npCR leaf probability:",
        pcr_leaf.probability
    )

    print(
        "pCR leaf prediction:",
        pcr_leaf.prediction
    )

    print(
        "pCR node is leaf:",
        pcr_leaf.is_leaf()
    )


    """Тест т. 8 за функцията should_stop."""
    print("\nTesting should_stop:")

    # Случай 1:
    # всички пациенти са RD,
    # следователно групата е чиста.
    pure_group = np.array([
        0,
        0,
        0
    ])

    stop_pure = should_stop(
        pure_group,
        current_depth=0,
        max_depth=3,
        min_samples_split=2
    )

    print(
        "Stop pure group:",
        stop_pure
    )

    # Случай 2:
    # групата е смесена и има достатъчно пациенти.
    mixed_group = np.array([
        0,
        0,
        1,
        1
    ])

    stop_mixed = should_stop(
        mixed_group,
        current_depth=0,
        max_depth=3,
        min_samples_split=2
    )

    print(
        "Stop mixed group:",
        stop_mixed
    )

    # Случай 3:
    # достигната е максималната дълбочина.
    stop_max_depth = should_stop(
        mixed_group,
        current_depth=3,
        max_depth=3,
        min_samples_split=2
    )

    print(
        "Stop at maximum depth:",
        stop_max_depth
    )

    # Случай 4:
    # останал е само един пациент.
    small_group = np.array([
        1
    ])

    stop_small_group = should_stop(
        small_group,
        current_depth=1,
        max_depth=3,
        min_samples_split=2
    )

    print(
        "Stop small group:",
        stop_small_group
    )


    """Тест т. 8 за функцията should_stop с празна група."""
    empty_group = np.array([])

    stop_empty_group = should_stop(
        empty_group,
        current_depth=0,
        max_depth=3,
        min_samples_split=2
    )

    print(
        "Stop empty group:",
        stop_empty_group
    )

    """Стъпка 9 — build_tree()"""
    print("\nTesting build_tree:")

    tree = build_tree(
        X_test,
        y_test,
        max_depth=3,
        min_samples_split=2
    )

    print(
        "Root is leaf:",
        tree.is_leaf()
    )

    print(
        "Root feature index:",
        tree.feature_index
    )

    print(
        "Root threshold:",
        tree.threshold
    )

    print(
        "Root probability:",
        tree.probability
    )

    print(
        "Root prediction:",
        tree.prediction
    )

    print(
        "Left child is leaf:",
        tree.left.is_leaf()
    )

    print(
        "Left child prediction:",
        tree.left.prediction
    )

    print(
        "Left child probability:",
        tree.left.probability
    )

    print(
        "Right child is leaf:",
        tree.right.is_leaf()
    )

    print(
        "Right child prediction:",
        tree.right.prediction
    )

    print(
        "Right child probability:",
        tree.right.probability
    )


    print("\nTesting predict_one:")

    # Списъци, в които ще съберем
    # прогнозите за всички пациенти.
    tree_predictions = []
    tree_probabilities = []

    # Обхождаме примерните пациенти
    # един по един.
    for patient_index in range(
        len(X_test)
    ):
        # Взимаме един ред от X_test.
        patient = X_test[
            patient_index
        ]

        # Получаваме прогнозата
        # и вероятността от дървото.
        (
            prediction,
            probability
        ) = predict_one(
            tree,
            patient
        )

        tree_predictions.append(
            prediction
        )

        tree_probabilities.append(
            probability
        )

        print(
            "Patient",
            patient_index,
            "| Actual:",
            y_test[patient_index],
            "| Predicted:",
            prediction,
            "| pCR probability:",
            probability
        )

    print(
        "\nAll predictions:",
        tree_predictions
    )

    print(
        "All probabilities:",
        tree_probabilities
    )

    """Тест Стъпка 10 — predict_tree()"""

    print("\nTesting predict_tree:")

    (
        predictions,
        probabilities
    ) = predict_tree(
        tree,
        X_test
    )

    print(
        "Actual classes:",
        y_test
    )

    print(
        "Predicted classes:",
        predictions
    )

    print(
        "pCR probabilities:",
        probabilities
    )

    # Проверяваме колко прогнози
    # съвпадат с реалните класове.
    correct_predictions = np.sum(
        predictions == y_test
    )

    accuracy = (
        correct_predictions / len(y_test)
    )

    print(
        "Accuracy:",
        accuracy
    )

    """Тест Стъпка 8 — select_random_features()"""

    print(
        "\nTesting select_random_features:"
    )

    test_random_generator = (
        np.random.RandomState(42)
    )

    selected_features = select_random_features(
        number_of_features=10,
        max_features=3,
        random_generator=test_random_generator
    )

    print(
        "Selected feature indices:",
        selected_features
    )

    print(
        "Number of selected features:",
        len(selected_features)
    )

    print(
        "No repeated features:",
        len(selected_features)
        ==
        len(set(selected_features))
    )