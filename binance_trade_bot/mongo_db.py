from pymongo.errors import InvalidName


class MongoBinanceTraderManager:
    TRADING_PAIR = "BTC"

    @staticmethod
    def get_query_object(symbol):
        return {
            "key": f"{symbol + MongoBinanceTraderManager.TRADING_PAIR}-last-buy-price"
        }

    def __init__(self, mongodb_client, logger):
        self.mongodb_client = mongodb_client
        self.logger = logger
        try:
            self.trailing_bot_db = self.mongodb_client["binance-bot"]
        except InvalidName:
            self.logger.error("Error: Please start the trailing_bot, binance-bot db can't be found")
        self.db_col = self.trailing_bot_db["trailing-trade-symbols"]

    def _get_last_buy_price_quantity(self, from_symbol):
        query = self.get_query_object(from_symbol)
        last_bought = self.db_col.find_one(filter=query)
        if last_bought:
            return last_bought["lastBuyPrice"], last_bought["quantity"]
        else:
            return 0, 0

    def _drop_last_buy_price(self, from_symbol):
        query = self.get_query_object(from_symbol)
        self.logger.info(f"Last Buy Price of {from_symbol}/BTC has been reset")
        self.db_col.delete_one(filter=query)

    def _update_mongodb_last_buy_price(self, symbol, buy_price, quantity):
        new_values = {
            "$set": {
                "key": f"{symbol + self.TRADING_PAIR}-last-buy-price",
                "lastBuyPrice": buy_price,
                "quantity": quantity
            }
        }
        query = self.get_query_object(symbol)
        self.db_col.update_one(query, new_values, upsert=True)

    def execute_trx(self, from_symbol, to_symbol, quantity, price_value):
        from_last_price, from_last_quantity = self._get_last_buy_price_quantity(from_symbol)
        if from_last_price == 0:
            total_spent = price_value * quantity
        else:
            total_spent = from_last_price * from_last_quantity

        to_last_price, to_last_quantity = self._get_last_buy_price_quantity(to_symbol)
        total_exists = to_last_price * to_last_quantity

        total_quantity = quantity + to_last_quantity

        # 1.015 is a binance fee Coin A -> Bridge -> Coin B
        avg_price = (total_exists + total_spent) * 1.015 / total_quantity
        self._drop_last_buy_price(from_symbol)
        self._update_mongodb_last_buy_price(to_symbol, avg_price, total_quantity)
        self.logger.info(f"AVG Last Buy Price of {avg_price:0.10f} for {to_symbol}/BTC in total amount of {total_quantity:0.10f} is persisted in mongodb")

