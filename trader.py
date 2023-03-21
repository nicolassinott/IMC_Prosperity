from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order

PEARL_PRICE = 10000

class Trader:

    def __init__(self) -> None:
        # self.position = {
        #     "PEARLS" : 0,
        #     "BANANAS": 0
        # }
        self.pearl_position_limit = 20

        self.last_orders = {
            'BANANAS': {
                'BID' : set(),
                'ASK' : set()
            },
            'PEARLS' : {
                'BID' : set(),
                'ASK' : set()
            }
        }

        self.pnl = 0

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}
        
        position_pearls = state.position['PEARLS'] if 'PEARLS' in state.position else 0
        position_bananas = state.position['BANANAS'] if 'BANANAS' in state.position else 0

        pnl = 0
        
        if 'PEARLS' in state.own_trades.keys():
            total_trades = state.own_trades['PEARLS']

            if 'PEARLS' in state.order_depths.keys():
                market_trades_pearls_bid = state.order_depths['PEARLS'].buy_orders
                market_trades_pearls_ask = state.order_depths['PEARLS'].sell_orders

                best_ask = min(market_trades_pearls_ask.keys())
                best_bid = max(market_trades_pearls_bid.keys())

                mid_price_pearl = (best_ask + best_bid)/2

                print(f"Mid price: {mid_price_pearl}")
                for trade in total_trades:
                    if trade.timestamp == state.timestamp - 100:
                        if trade.price < PEARL_PRICE:
                            print(f"trade: {trade}")
                            pnl += trade.quantity * (PEARL_PRICE - trade.price)
                        else:
                            print(f"trade: {trade}")
                            pnl -= trade.quantity * (PEARL_PRICE - trade.price)

            # self.last_orders['PEARLS']['BID'] = set()
            # self.last_orders['PEARLS']['ASK'] = set()

        if 'BANANAS' in state.own_trades.keys():
            total_trades = state.own_trades['BANANAS']

            if 'BANANAS' in state.order_depths.keys():
                market_trades_bananas_bid = state.order_depths['BANANAS'].buy_orders
                market_trades_bananas_ask = state.order_depths['BANANAS'].sell_orders

                best_bid = max(market_trades_bananas_bid.keys())
                best_ask = min(market_trades_bananas_ask.keys())

                mid_price_bananas = (best_ask + best_bid)/2

                print(f"Mid price: {mid_price_bananas}")
                for trade in total_trades:
                    if trade.timestamp == state.timestamp - 100:
                        if trade.price in self.last_orders['BANANAS']['BID']: # Must correct as bid might be below bid price sent (!!!)
                            print(f"trade: {trade}")
                            pnl += trade.quantity * (mid_price_bananas - trade.price)
                        else:
                            print(f"trade: {trade}")
                            pnl -= trade.quantity * (mid_price_bananas - trade.price)

            self.last_orders['BANANAS']['BID'] = set()
            self.last_orders['BANANAS']['ASK'] = set()

        self.pnl += pnl

        print(f"PNL = {self.pnl}")

        # Iterate over all the keys (the available products) contained in the order depths

        for product in state.order_depths.keys():
            if product == 'PEARLS':
                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []

                best_bid = PEARL_PRICE - 1
                bid_volume = self.pearl_position_limit - position_pearls
                orders.append(Order(product, best_bid, bid_volume))

                best_ask = PEARL_PRICE + 1
                ask_volume = - self.pearl_position_limit - position_pearls
                orders.append(Order(product, best_ask, ask_volume))

                # if len(order_depth.buy_orders) > 0:
                #     best_bid = max(order_depth.buy_orders.keys()) + 1
                #     best_bid = PEARL_PRICE - 1
                #     if best_bid < PEARL_PRICE:
                #         bid_volume = self.pearl_position_limit - position_pearls
                #         print(f"Inserting bid order {Order(product, best_bid, bid_volume)}")
                #         orders.append(Order(product, best_bid, bid_volume))
                #         self.last_orders['PEARLS']['BID'].add(best_bid)
                # if len(order_depth.sell_orders) > 0:
                #     best_ask = min(order_depth.sell_orders.keys()) - 1
                #     best_ask = PEARL_PRICE + 1
                #     if best_ask > PEARL_PRICE:
                #         ask_volume = -self.pearl_position_limit - position_pearls
                #         print(f"Inserting ask order {Order(product, best_ask, ask_volume)}")
                #         orders.append(Order(product, best_ask, ask_volume))
                #         self.last_orders['PEARLS']['ASK'].add(best_ask)

                result[product] = orders

        return result

        for product in state.order_depths.keys():

            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':

                # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
                order_depth: OrderDepth = state.order_depths[product]

                # Initialize the list of Orders to be sent as an empty list
                orders: list[Order] = []

                # Define a fair value for the PEARLS.
                # Note that this value of 1 is just a dummy value, you should likely change it!
                acceptable_price = 1

                # If statement checks if there are any SELL orders in the PEARLS market
                if len(order_depth.sell_orders) > 0:

                    # Sort all the available sell orders by their price,
                    # and select only the sell order with the lowest price
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = order_depth.sell_orders[best_ask]

                    # Check if the lowest ask (sell order) is lower than the above defined fair value
                    if best_ask < acceptable_price:

                        # In case the lowest ask is lower than our fair value,
                        # This presents an opportunity for us to buy cheaply
                        # The code below therefore sends a BUY order at the price level of the ask,
                        # with the same quantity
                        # We expect this order to trade with the sell order
                        # print("BUY", str(-best_ask_volume) + "x", best_ask)
                        orders.append(Order(product, best_ask, -best_ask_volume))

                # The below code block is similar to the one above,
                # the difference is that it finds the highest bid (buy order)
                # If the price of the order is higher than the fair value
                # This is an opportunity to sell at a premium
                if len(order_depth.buy_orders) != 0:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = order_depth.buy_orders[best_bid]
                    if best_bid > acceptable_price:
                        # print("SELL", str(best_bid_volume) + "x", best_bid)
                        orders.append(Order(product, best_bid, -best_bid_volume))

                # Add all the above orders to the result dict
                result[product] = orders

                # Return the dict of orders
                # These possibly contain buy or sell orders for PEARLS
                # Depending on the logic above
        return result