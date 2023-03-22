from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order

import math

# storing string as const to avoid typos
SUBMISSION = "SUBMISSION"
PEARLS = "PEARLS"
BANANAS = "BANANAS"

PRODUCTS = [
    PEARLS,
    BANANAS,
]

DEFAULT_PRICES = {
    PEARLS : 10_000,
    BANANAS : 5_000,
}

class Trader:

    def __init__(self) -> None:
        
        print("Initializing Trader...")

        self.position_limit = {
            PEARLS : 20,
            BANANAS : 20,
        }

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

        bid_volume = self.position_limit[PEARLS] - position_pearls
        ask_volume = - self.position_limit[PEARLS] - position_pearls

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

        bid_volume = self.position_limit[BANANAS] - position_bananas
        ask_volume = - self.position_limit[BANANAS] - position_bananas

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

        # PEARL STRATEGY
        try:
            result[PEARLS] = self.pearls_strategy(state)
        except Exception as e:
            print("Error in pearls strategy")
            print(e)

        # BANANA STRATEGY
        try:
            result[BANANAS] = self.bananas_strategy(state)
        except Exception as e:
            print("Error in bananas strategy")
            print(e)

        print("+---------------------------------+")

        return result