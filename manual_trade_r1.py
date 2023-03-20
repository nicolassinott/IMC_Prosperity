import copy

EXCHANGE_MATRIX = [
    [1, 0.5, 1.45, 0.75],
    [1.95, 1, 3.1, 1.49],
    [0.67, 0.31, 1, 0.48],
    [1.34, 0.64, 1.98, 1],
]

# Maximum amount of each asset possible after trades

MAX_AMOUNT = [0, 0, 0, 2_000_000]
BEST_ROUTE = [[], [], [], []]

# There are 5 trades
for _ in range(5):
    NEW_MAX_AMOUNT = copy.deepcopy(MAX_AMOUNT)
    NEW_BEST_ROUTE = copy.deepcopy(BEST_ROUTE)

    for target_product in range(4):
        for origin_product in range(4):
            quantity_target = MAX_AMOUNT[origin_product] * EXCHANGE_MATRIX[origin_product][target_product]
            if quantity_target > NEW_MAX_AMOUNT[target_product]:
                NEW_MAX_AMOUNT[target_product] = quantity_target
                NEW_BEST_ROUTE[target_product] = BEST_ROUTE[origin_product] + [(origin_product, target_product)]

    MAX_AMOUNT = NEW_MAX_AMOUNT
    BEST_ROUTE = NEW_BEST_ROUTE

print(MAX_AMOUNT)