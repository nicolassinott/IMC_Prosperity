from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import pandas as pd
import numpy as np
import math

# storing string as const to avoid typos
SUBMISSION = "SUBMISSION"
PEARLS = "PEARLS"
BANANAS = "BANANAS"
COCONUTS = "COCONUTS"
PINA_COLADAS = "PINA_COLADAS"
BERRIES = "BERRIES"
DIVING_GEAR = "DIVING_GEAR"
DOLPHIN_SIGHTINS = "DOLPHIN_SIGHTINS"


PRODUCTS = [
    PEARLS,
    BANANAS,
    COCONUTS,
    PINA_COLADAS,
    BERRIES,
    DIVING_GEAR,
    DOLPHIN_SIGHTINS 
]

DEFAULT_PRICES = {
    PEARLS : 10_000,
    BANANAS : 5_000,
    COCONUTS : 8_000,
    PINA_COLADAS : 15_000,
    BERRIES : 3_900,
    DIVING_GEAR : 99_000,
    DOLPHIN_SIGHTINS : 3_050
}

POSITION_LIMITS = {
    COCONUTS: 600,
    PINA_COLADAS: 300,
    BERRIES: 250
}

ORDER_VOLUME = 5

TAKE_PROFIT = 10
STOP_LOSS = 30
WINDOW = 200

MEAN_SPREAD = DEFAULT_PRICES[PINA_COLADAS] - DEFAULT_PRICES[COCONUTS]
MEAN_SPREAD_STD = 30

class Trader:

    def __init__(self) -> None:
        
        print("Initializing Trader... ok")

        self.position_limit = {
            PEARLS : 20,
            BANANAS : 20,
            "COCONUTS_EMA": 300
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

        self.prices : Dict[PRODUCTS, pd.Series] = {
            PINA_COLADAS: pd.Series(),
            COCONUTS: pd.Series(),
            "Spread":pd.Series()
        }

        self.all_positions = set()
        self.coconuts_pair_position = 0

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

    def save_prices(self, state: TradingState):
        price_coconut = self.get_mid_price(COCONUTS, state)
        price_pina_colada = self.get_mid_price(PINA_COLADAS, state)

        self.prices[COCONUTS] = pd.concat([
            self.prices[COCONUTS], 
            pd.Series({state.timestamp: price_coconut})
        ])

        self.prices[PINA_COLADAS] = pd.concat([
            self.prices[PINA_COLADAS],
            pd.Series({state.timestamp: price_pina_colada})
        ])

        # # linreg to get b value
        # X = self.prices[COCONUTS].copy().to_frame()
        # X["const"] = 1
        # y = self.prices[PINA_COLADAS].copy()
        # # B = (XtX)^-1 Xt y
        # B = np.linalg.multi_dot([np.linalg.inv(np.dot(X.transpose(),X)), X.transpose(), y])

        self.prices["Spread"] = self.prices[PINA_COLADAS] - 1.551*self.prices[COCONUTS]

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
    
    def coconuts_pina_coladas_strategy(self, state : TradingState) -> List[List[Order]]:
        """Performs statistical arbitrage between coconuts and pina coladas.
        Verifies if the (rolling5 - rolling50)/std50 of the spread is bigger 
        than 2 (or smaller than -2).

        Args:
            state (TradingState): _description_

        Returns:
            _type_: _description_
        """        
        orders_coconuts : List = []
        orders_pina_coladas : List = []

        self.save_prices(state) 

        mid_price_coconuts = self.get_mid_price(COCONUTS, state)
        mid_price_pina_coladas = self.get_mid_price(PINA_COLADAS, state)
        spread = mid_price_pina_coladas - mid_price_coconuts

        int_price_coconuts = int(mid_price_coconuts)
        int_price_pina_coladas = int(mid_price_pina_coladas)

        # coconuts_position = self.get_position(COCONUTS, state)
        coconuts_position = self.coconuts_pair_position
        pina_coladas_position = self.get_position(PINA_COLADAS, state)

        #if pina_coladas_position != -coconuts_position:
        #    print(f"WRONG: pina_colada: {pina_coladas_position}, coconuts: {coconuts_position}")

        avg_spread = self.prices["Spread"].rolling(WINDOW).mean()
        std_spread = self.prices["Spread"].rolling(WINDOW).std()
        spread_5 = self.prices["Spread"].rolling(5).mean()

        if not np.isnan(avg_spread.iloc[-1]):
            avg_spread = avg_spread.iloc[-1]
            std_spread = std_spread.iloc[-1]
            spread_5 = spread_5.iloc[-1]
            print(f"Average spread: {avg_spread}, Spread5: {spread_5}, Std: {std_spread}")

            if abs(coconuts_position) < POSITION_LIMITS[COCONUTS]-30:
                if spread_5 < avg_spread - 1.5*std_spread: # buy 
                    orders_coconuts.append(Order(COCONUTS, int_price_coconuts-2, -2*ORDER_VOLUME))
                    orders_pina_coladas.append(Order(PINA_COLADAS, int_price_pina_coladas+3, ORDER_VOLUME))
                    self.coconuts_pair_position -= ORDER_VOLUME
                     
                elif spread_5 > avg_spread + 1.5*std_spread: # sell
                    orders_coconuts.append(Order(COCONUTS, int_price_coconuts+3, 2*ORDER_VOLUME))
                    orders_pina_coladas.append(Order(PINA_COLADAS, int_price_pina_coladas-2, -ORDER_VOLUME))
                    self.coconuts_pair_position += ORDER_VOLUME

            else: # abs(coconuts_position) >= POSITION_LIMITS[COCONUTS] - 30
                if coconuts_position > 0:
                    if spread_5 < avg_spread - 1.5*std_spread:
                        orders_coconuts.append(Order(COCONUTS, int_price_coconuts-2, -2*ORDER_VOLUME))
                        orders_pina_coladas.append(Order(PINA_COLADAS, int_price_pina_coladas+3, ORDER_VOLUME))
                        self.coconuts_pair_position -= ORDER_VOLUME
                else :
                    if spread_5 > avg_spread + 1.5*std_spread:
                        orders_coconuts.append(Order(COCONUTS, int_price_coconuts+3, 2*ORDER_VOLUME))
                        orders_pina_coladas.append(Order(PINA_COLADAS, int_price_pina_coladas-2, -ORDER_VOLUME))
                        self.coconuts_pair_position += ORDER_VOLUME

        return orders_coconuts, orders_pina_coladas
    
    def coconut_strategy(self, state: TradingState):
        position_coconuts = self.get_position(COCONUTS, state) - self.coconuts_pair_position

        bid_volume = min(40, self.position_limit["COCONUTS_EMA"] - position_coconuts)
        ask_volume = max(-40, -self.position_limit["COCONUTS_EMA"] - position_coconuts)

        orders = []

        if position_coconuts == 0:
            # Not long nor short
            orders.append(Order(COCONUTS, math.floor(self.ema_prices[COCONUTS] - 1), bid_volume))
            orders.append(Order(COCONUTS, math.ceil(self.ema_prices[COCONUTS] + 1), ask_volume))
            
        
        if position_coconuts > 0:
            # Long position
            orders.append(Order(COCONUTS, math.floor(self.ema_prices[COCONUTS] - 2), bid_volume))
            orders.append(Order(COCONUTS, math.ceil(self.ema_prices[COCONUTS]), ask_volume))

        if position_coconuts < 0:
            # Short position
            orders.append(Order(COCONUTS, math.floor(self.ema_prices[COCONUTS]), bid_volume))
            orders.append(Order(COCONUTS, math.ceil(self.ema_prices[COCONUTS] + 2), ask_volume))

        return orders

    def berries_strategy(self, state: TradingState)-> List[Order]:
        """Berries strategy. 
        We will send only two orders: 
        
        * Buy orders near timestamp == 2e5
        * Sell orders near timestamp == 5e5

        Args:
            state (TradingState): _description_

        Returns:
            List[Order]: _description_
        """        
        order_berries = []
        position_berries = self.get_position(BERRIES, state)

        if abs(state.timestamp - 2e5) <= 800:
            if POSITION_LIMITS[BERRIES] - position_berries > 0:
                volume = min(POSITION_LIMITS[BERRIES]- position_berries, 40)
                order_berries.append(
                    Order(BERRIES, 1e4, volume)
                )
            
        if abs(state.timestamp - 5e5) <= 800:
            if position_berries + POSITION_LIMITS[BERRIES] > 0:
                volume = max(-POSITION_LIMITS[BERRIES] - position_berries, -40)
                order_berries.append(
                    Order(BERRIES, 1, volume)
                )
        return order_berries

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

        # COCONUTS AND PINA COLADAS STRATEGY
        try:
            result[COCONUTS], result[PINA_COLADAS] = self.coconuts_pina_coladas_strategy(state)

            
        except Exception as e:
            print("Error in coconuts and pina coladas strategy")
            print(e)

        try:
            result[BERRIES] = self.berries_strategy(state)

        except Exception as e:
            print("Error in Berries strategy")
            print(e)

        
        print("+---------------------------------+")

        return result