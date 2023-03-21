from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order

import math

# storing string as const to avoid typos
SUBMISSION = "SUBMISSION"
PEARLS = "PEARLS"
BANANAS = "BANANAS"
COCONUTS = "COCONUTS"
PINA_COLADAS = "PINA_COLADAS"


PRODUCTS = [
    PEARLS,
    BANANAS,
    COCONUTS,
    PINA_COLADAS
]

DEFAULT_PRICES = {
    PEARLS : 10_000,
    BANANAS : 5_000,
    COCONUTS : 8_000,
    PINA_COLADAS : 15_000
}

POSITION_LIMITS = {
    PEARLS : 20,
    BANANAS : 20,
    COCONUTS : 600,
    PINA_COLADAS : 300,
}

MEAN_SPREAD = DEFAULT_PRICES[PINA_COLADAS] - DEFAULT_PRICES[COCONUTS]
MEAN_SPREAD_STD = 10

# Coeff for LinReg Model 
# PINA_COLADA = COEF_1 * COCONUT + COEF_0
COEF_1 = 1.551
COEF_0 = 2593


def fast_order(product, price, quantity):
    """
    Creates an order of the desired product, for the desired quantity. The
    price is rounded to an integer.

    If the order is a buy order, price is rounded up. Otherwise price is 
    rounded down.

    The idea behind this order is to get the order executed quickly by rounding
    the price appropriately.
    """

    if quantity < 0:
        price = math.floor(price)
    else:
        price = math.ceil(price)

    return Order(product, price, quantity)

class Trader:

    def __init__(self) -> None:
        
        print("Initializing Trader...")

        self.round = 0

        # Values to compute pnl
        self.cash = 0
        # positions can be obtained from state.position
        
        # self.past_prices keeps the list of all past prices
        self.past_prices = dict()
        for product in PRODUCTS:
            self.past_prices[product] = []

        # self.ema_prices keeps an exponential moving average of prices
        self.ema_prices = dict()
        for product in PRODUCTS:
            self.ema_prices[product] = None

        self.ema_param = 0.5


    # utils
    def get_position(self, product, state : TradingState):
        return state.position.get(product, 0)    

    def get_mid_price(self, product, state : TradingState):

        default_price = self.ema_prices[product]
        if default_price is None:
            default_price = DEFAULT_PRICES[product]

        if product not in state.order_depths:
            return default_price

        market_bids = state.order_depths[product].buy_orders
        if len(market_bids) == 0:
            # There are no bid orders in the market (midprice undefined)
            return default_price
        
        market_asks = state.order_depths[product].sell_orders
        if len(market_asks) == 0:
            # There are no bid orders in the market (mid_price undefined)
            return default_price
        
        best_bid = max(market_bids)
        best_ask = min(market_asks)
        return (best_bid + best_ask)/2

    def get_value_on_product(self, product, state : TradingState):
        """
        Returns the amount of MONEY currently held on the product.  
        """
        return self.get_position(product, state) * self.get_mid_price(product, state)
            
    def update_pnl(self, state : TradingState):
        """
        Updates the pnl.
        """
        def update_cash():
            # Update cash
            for product in state.own_trades:
                for trade in state.own_trades[product]:
                    if trade.timestamp != state.timestamp - 100:
                        # Trade was already analyzed
                        continue

                    if trade.buyer == SUBMISSION:
                        self.cash -= trade.quantity * trade.price
                    if trade.seller == SUBMISSION:
                        self.cash += trade.quantity * trade.price
        
        def get_value_on_positions():
            value = 0
            for product in state.position:
                value += self.get_value_on_product(product, state)
            return value
        
        # Update cash
        update_cash()
        return self.cash + get_value_on_positions()

    def update_ema_prices(self, state : TradingState):
        """
        Update the exponential moving average of the prices of each product.
        """
        for product in PRODUCTS:
            mid_price = self.get_mid_price(product, state)
            if mid_price is None:
                continue

            # Update ema price
            if self.ema_prices[product] is None:
                self.ema_prices[product] = mid_price
            else:
                self.ema_prices[product] = self.ema_param * mid_price + (1-self.ema_param) * self.ema_prices[product]


    # Algorithm logic
    def pearls_strategy(self, state : TradingState):
        """
        Returns a list of orders with trades of pearls.

        Comment: Mudar depois. Separar estrategia por produto assume que
        cada produto eh tradado independentemente
        """

        position_pearls = self.get_position(PEARLS, state)

        bid_volume = POSITION_LIMITS[PEARLS] - position_pearls
        ask_volume = - POSITION_LIMITS[PEARLS] - position_pearls

        orders = []
        orders.append(Order(PEARLS, DEFAULT_PRICES[PEARLS] - 1, bid_volume))
        orders.append(Order(PEARLS, DEFAULT_PRICES[PEARLS] + 1, ask_volume))

        return orders

    def bananas_strategy(self, state : TradingState):
        """
        Returns a list of orders with trades of bananas.

        Comment: Mudar depois. Separar estrategia por produto assume que
        cada produto eh tradado independentemente
        """

        position_bananas = self.get_position(BANANAS, state)

        bid_volume = POSITION_LIMITS[BANANAS] - position_bananas
        ask_volume = - POSITION_LIMITS[BANANAS] - position_bananas

        orders = []

        if position_bananas == 0:
            # Not long nor short
            orders.append(Order(BANANAS, math.floor(self.ema_prices[BANANAS] - 1), bid_volume))
            orders.append(Order(BANANAS, math.ceil(self.ema_prices[BANANAS] + 1), ask_volume))
        
        if position_bananas > 0:
            # Long position
            orders.append(Order(BANANAS, math.floor(self.ema_prices[BANANAS] - 2), bid_volume))
            orders.append(Order(BANANAS, math.ceil(self.ema_prices[BANANAS]), ask_volume))

        if position_bananas < 0:
            # Short position
            orders.append(Order(BANANAS, math.floor(self.ema_prices[BANANAS]), bid_volume))
            orders.append(Order(BANANAS, math.ceil(self.ema_prices[BANANAS] + 2), ask_volume))

        return orders
    
    def coconuts_pina_coladas_strategy(self, state : TradingState):
        orders_coconuts = []
        orders_pina_coladas = []
        
        mid_price_coconuts = self.get_mid_price(COCONUTS, state)
        mid_price_pina_coladas = self.get_mid_price(PINA_COLADAS, state)
        spread = mid_price_pina_coladas - mid_price_coconuts

        coconuts_position = self.get_position(COCONUTS, state)
        pina_coladas_position = self.get_position(PINA_COLADAS, state)

        if pina_coladas_position != -coconuts_position:
            print(f"WRONG: pina_colada: {pina_coladas_position}, coconuts: {coconuts_position}")

        if coconuts_position == 0:
            if spread < MEAN_SPREAD - MEAN_SPREAD_STD:
                orders_coconuts.append(Order(COCONUTS, 1, -40))
                orders_pina_coladas.append(Order(PINA_COLADAS, 1e5, 40))
            elif spread > MEAN_SPREAD + MEAN_SPREAD_STD:
                orders_coconuts.append(Order(COCONUTS, 1e5, 40))
                orders_pina_coladas.append(Order(PINA_COLADAS, 1, -40))
        
        elif coconuts_position < 0:
            if spread > MEAN_SPREAD:
                orders_coconuts.append(Order(COCONUTS, 1e5, -coconuts_position))
                orders_pina_coladas.append(Order(PINA_COLADAS, 1, coconuts_position))

        else: # coconuts_position > 0
            if spread < MEAN_SPREAD:
                orders_coconuts.append(Order(COCONUTS, 1, -coconuts_position))
                orders_pina_coladas.append(Order(PINA_COLADAS, 1e5, coconuts_position))

        return orders_coconuts, orders_pina_coladas


    def coconut_pina_colada_linreg_strategy(self, state : TradingState):
        # First strategy - no attempt to stay hedged

        # Acochambrada:
        POSITION_LIMITS[COCONUTS] = int(POSITION_LIMITS[PINA_COLADAS] * COEF_1)

        orders_coconuts = []
        orders_pina_coladas = []
        
        mid_price_coconuts = self.get_mid_price(COCONUTS, state)
        mid_price_pina_coladas = self.get_mid_price(PINA_COLADAS, state)

        coconuts_position = self.get_position(COCONUTS, state)
        pina_coladas_position = self.get_position(PINA_COLADAS, state)

        # Predicted "fair" pina colada price
        fair_price = mid_price_coconuts * COEF_1 + COEF_0

        # Margin of safety
        MARGIN = 5

        print("PINA-COCONUT STATS:")
        print("COCONUT MIDPRICE", mid_price_coconuts)
        print("PINA_COLADA MIDPRICE", mid_price_pina_coladas)
        print("FAIR PRICE", fair_price)
        
        if fair_price > mid_price_pina_coladas + MARGIN:
            print("Signal - pina is cheap")
            # Pina coladas are cheap -> buy pina and sell coconuts
            size_coconut = -POSITION_LIMITS[COCONUTS] - coconuts_position
            size_pina_coladas = POSITION_LIMITS[PINA_COLADAS] - pina_coladas_position

            orders_coconuts.append(fast_order(COCONUTS, mid_price_coconuts-0.5, size_coconut))
            orders_pina_coladas.append(fast_order(PINA_COLADAS, mid_price_pina_coladas+0.5, size_pina_coladas))

        elif fair_price < mid_price_pina_coladas - MARGIN:
            print("Signal - pina is expensive")
            # Pina coladas are expensive -> sell pina and buy coconuts
            size_coconut = POSITION_LIMITS[COCONUTS] - coconuts_position
            size_pina_coladas = -POSITION_LIMITS[PINA_COLADAS] - pina_coladas_position

            orders_coconuts.append(fast_order(COCONUTS, mid_price_coconuts+0.5, size_coconut))
            orders_pina_coladas.append(fast_order(PINA_COLADAS, mid_price_pina_coladas-0.5, size_pina_coladas))
        
        else:
            print("Signal - pina is ok")
            # Price relation seems fair - time to get hedged
            orders_coconuts.append(fast_order(COCONUTS, mid_price_coconuts, -coconuts_position))
            orders_pina_coladas.append(fast_order(PINA_COLADAS, mid_price_pina_coladas, -pina_coladas_position))

        print("Orders submitted pina-coconut")
        print(orders_coconuts)
        print(orders_pina_coladas)

        return orders_coconuts, orders_pina_coladas

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """

        self.round += 1
        pnl = self.update_pnl(state)
        self.update_ema_prices(state)

        print(f"Log round {self.round}")

        print("TRADES:")
        for product in state.own_trades:
            for trade in state.own_trades[product]:
                if trade.timestamp == state.timestamp - 100:
                    print(trade)

        print(f"\tCash {self.cash}")
        for product in PRODUCTS:
            print(f"\tProduct {product}, Position {self.get_position(product, state)}, Midprice {self.get_mid_price(product, state)}, Value {self.get_value_on_product(product, state)}, EMA {self.ema_prices[product]}")
        print(f"\tPnL {pnl}")
        

        # Initialize the method output dict as an empty dict
        result = {}

        # # PEARL STRATEGY
        # try:
        #     result[PEARLS] = self.pearls_strategy(state)
        # except Exception as e:
        #     print("Error in pearls strategy")
        #     print(e)

        # # BANANA STRATEGY
        # try:
        #     result[BANANAS] = self.bananas_strategy(state)
        # except Exception as e:
        #     print("Error in bananas strategy")
        #     print(e)

        # COCONUTS AND PINA COLADAS STRATEGY
        try:
            result[COCONUTS], result[PINA_COLADAS] = self.coconut_pina_colada_linreg_strategy(state)
        except Exception as e:
            print("Error in coconuts and pina coladas strategy")
            print(e)

        print("+---------------------------------+")

        return result