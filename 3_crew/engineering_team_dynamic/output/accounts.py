def get_share_price(symbol):
    """Test implementation that returns fixed prices for AAPL, TSLA, GOOGL."""
    prices = {
        "AAPL": 150.25,
        "TSLA": 820.75,
        "GOOGL": 2750.50
    }
    return prices.get(symbol, 0.0)


class Account:
    """Class for managing user accounts in a trading simulation platform."""

    def __init__(self, user_id, initial_deposit=0.0):
        """Initialize a new account with user ID and optional initial deposit."""
        self.user_id = user_id
        self.balance = 0.0
        self.initial_deposit = 0.0
        self.holdings = {}
        self.transactions = []
        
        if initial_deposit > 0.0:
            self.deposit_funds(initial_deposit)

    def deposit_funds(self, amount):
        """Deposit funds into the account."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        self.balance += amount
        self.initial_deposit += amount
        
        transaction = {
            "type": "DEPOSIT",
            "amount": amount,
            "balance_after": self.balance
        }
        
        self.transactions.append(transaction)
        return self.balance

    def withdraw_funds(self, amount):
        """Withdraw funds from the account, ensuring balance doesn't become negative."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
            
        if amount > self.balance:
            raise ValueError(f"Insufficient funds: balance {self.balance} is less than withdrawal amount {amount}")
        
        self.balance -= amount
        
        transaction = {
            "type": "WITHDRAWAL",
            "amount": amount,
            "balance_after": self.balance
        }
        
        self.transactions.append(transaction)
        return self.balance

    def buy_shares(self, symbol, quantity):
        """Buy shares of a specified stock, ensuring sufficient funds."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        share_price = get_share_price(symbol)
        if share_price == 0.0:
            raise ValueError(f"Unknown or invalid stock symbol: {symbol}")
            
        total_cost = share_price * quantity
        
        if total_cost > self.balance:
            raise ValueError(f"Insufficient funds: balance {self.balance} is less than total cost {total_cost}")
            
        self.balance -= total_cost
        
        # Update holdings
        if symbol in self.holdings:
            self.holdings[symbol] += quantity
        else:
            self.holdings[symbol] = quantity
            
        transaction = {
            "type": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "price": share_price,
            "total_cost": total_cost,
            "balance_after": self.balance
        }
        
        self.transactions.append(transaction)
        return self.holdings[symbol]

    def sell_shares(self, symbol, quantity):
        """Sell shares of a specified stock, ensuring sufficient shares owned."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise ValueError(f"Insufficient shares: owns {self.holdings.get(symbol, 0)} but attempted to sell {quantity}")
            
        share_price = get_share_price(symbol)
        total_value = share_price * quantity
        
        self.balance += total_value
        self.holdings[symbol] -= quantity
        
        # Remove from holdings if quantity becomes 0
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
            
        transaction = {
            "type": "SELL",
            "symbol": symbol,
            "quantity": quantity,
            "price": share_price,
            "total_value": total_value,
            "balance_after": self.balance
        }
        
        self.transactions.append(transaction)
        return self.holdings.get(symbol, 0)

    def calculate_portfolio_value(self):
        """Calculate the total current value of the portfolio."""
        total_value = self.balance
        
        for symbol, quantity in self.holdings.items():
            share_price = get_share_price(symbol)
            total_value += share_price * quantity
            
        return total_value

    def calculate_profit_or_loss(self):
        """Calculate the total profit or loss based on initial deposits and current portfolio value."""
        current_value = self.calculate_portfolio_value()
        return current_value - self.initial_deposit

    def report_holdings(self):
        """Report the user's current holdings and balance."""
        holdings_report = {
            "cash_balance": self.balance,
            "shares": {}
        }
        
        for symbol, quantity in self.holdings.items():
            share_price = get_share_price(symbol)
            holdings_report["shares"][symbol] = {
                "quantity": quantity,
                "current_price": share_price,
                "current_value": share_price * quantity
            }
            
        holdings_report["total_value"] = self.calculate_portfolio_value()
        
        return holdings_report

    def report_profit_or_loss(self):
        """Report the user's current profit or loss."""
        profit_loss = self.calculate_profit_or_loss()
        
        return {
            "initial_deposit": self.initial_deposit,
            "current_value": self.calculate_portfolio_value(),
            "profit_or_loss": profit_loss,
            "profit_or_loss_percentage": (profit_loss / self.initial_deposit) * 100 if self.initial_deposit > 0 else 0
        }

    def list_transactions(self):
        """List all transactions made by the user."""
        return self.transactions


def create_account(user_id, initial_deposit=0.0):
    """Create a new user account with an initial deposit balance."""
    return Account(user_id, initial_deposit)