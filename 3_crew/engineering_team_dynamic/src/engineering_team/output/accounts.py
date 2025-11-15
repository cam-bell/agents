class Account:
    def __init__(self):
        # Initialize a new account
        self.balance = 0.0
        self.holdings = {}
        self.initial_deposit = 0.0
        self.transactions = []

    def deposit_funds(self, amount):
        if amount <= 0:
            raise ValueError('Deposit amount must be positive')
        self.balance += amount
        self.initial_deposit += amount
        self.transactions.append(("DEPOSIT", amount))

    def withdraw_funds(self, amount):
        if amount > self.balance:
            raise ValueError('Insufficient funds')
        if amount <= 0:
            raise ValueError('Withdrawal amount must be positive')
        self.balance -= amount
        self.transactions.append(("WITHDRAW", amount))

    def record_transaction(self, symbol, quantity):
        price = get_share_price(symbol)
        cost = price * quantity

        # Validate transaction
        if quantity > 0 and cost > self.balance:
            raise ValueError('Insufficient funds to buy shares')
        if quantity < 0 and self.holdings.get(symbol, 0) < abs(quantity):
            raise ValueError('Not enough shares to sell')

        # Update balance and holdings
        self.balance -= cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append(("BUY" if quantity > 0 else "SELL", symbol, quantity, price))

    def calculate_portfolio_value(self):
        return sum(get_share_price(symbol) * quantity for symbol, quantity in self.holdings.items())

    def calculate_profit_loss(self):
        return (self.calculate_portfolio_value() + self.balance) - self.initial_deposit

    def report_holdings(self):
        return dict(self.holdings)

    def report_profit_loss(self):
        return self.calculate_profit_loss()

    def list_transactions(self):
        return list(self.transactions)

def get_share_price(symbol):
    # Test implementation for share prices
    prices = {
        'AAPL': 150.0,
        'TSLA': 700.0,
        'GOOGL': 2800.0
    }
    return prices.get(symbol, 0)