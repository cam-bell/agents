from datetime import datetime
from enum import Enum, auto

# Test implementation of get_share_price function
def get_share_price(symbol):
    """Test implementation of the get_share_price function.
    Returns fixed prices for AAPL, TSLA, GOOGL, and raises ValueError for others.
    """
    prices = {
        'AAPL': 150.00,
        'TSLA': 800.00,
        'GOOGL': 2500.00
    }
    if symbol in prices:
        return prices[symbol]
    else:
        raise ValueError(f"Price not available for symbol: {symbol}")

# Define transaction types
class TransactionType(Enum):
    DEPOSIT = auto()
    WITHDRAWAL = auto()
    BUY = auto()
    SELL = auto()

class Account:
    def __init__(self, user_id):
        """
        Initialize a new account for the user.
        
        Args:
            user_id (str): A unique identifier for the user
        """
        self.user_id = user_id
        self.balance = 0.0
        self.portfolio = {}  # Symbol -> Quantity
        self.transactions = []  # List to store all transactions
        self.initial_deposit = 0.0  # To track profit/loss from initial deposit
    
    def deposit(self, amount):
        """
        Deposit funds into the account.
        
        Args:
            amount (float): The amount to deposit
            
        Returns:
            bool: True if the deposit was successful, False otherwise
        """
        if amount <= 0:
            return False
        
        # If this is the first deposit, update initial_deposit
        if self.balance == 0 and not self.transactions:
            self.initial_deposit = amount
        
        self.balance += amount
        
        # Record the transaction
        transaction = {
            'type': TransactionType.DEPOSIT,
            'amount': amount,
            'timestamp': datetime.now(),
            'details': f"Deposit of ${amount:.2f}"
        }
        self.transactions.append(transaction)
        
        return True
    
    def withdraw(self, amount):
        """
        Withdraw funds from the account.
        
        Args:
            amount (float): The amount to withdraw
            
        Returns:
            bool: True if the withdrawal was successful, False otherwise
        """
        if amount <= 0 or amount > self.balance:
            return False
        
        self.balance -= amount
        
        # Record the transaction
        transaction = {
            'type': TransactionType.WITHDRAWAL,
            'amount': amount,
            'timestamp': datetime.now(),
            'details': f"Withdrawal of ${amount:.2f}"
        }
        self.transactions.append(transaction)
        
        return True
    
    def buy_shares(self, symbol, quantity):
        """
        Buy shares of a stock.
        
        Args:
            symbol (str): The stock symbol
            quantity (int): The number of shares to buy
            
        Returns:
            bool: True if the purchase was successful, False otherwise
        """
        if quantity <= 0:
            return False
        
        try:
            price = get_share_price(symbol)
            total_cost = price * quantity
            
            # Check if user has enough balance
            if total_cost > self.balance:
                return False
            
            # Update balance
            self.balance -= total_cost
            
            # Update portfolio
            if symbol in self.portfolio:
                self.portfolio[symbol] += quantity
            else:
                self.portfolio[symbol] = quantity
            
            # Record the transaction
            transaction = {
                'type': TransactionType.BUY,
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'total': total_cost,
                'timestamp': datetime.now(),
                'details': f"Bought {quantity} shares of {symbol} at ${price:.2f} each, total: ${total_cost:.2f}"
            }
            self.transactions.append(transaction)
            
            return True
            
        except ValueError as e:
            # Handle case where symbol is invalid
            return False
    
    def sell_shares(self, symbol, quantity):
        """
        Sell shares of a stock.
        
        Args:
            symbol (str): The stock symbol
            quantity (int): The number of shares to sell
            
        Returns:
            bool: True if the sale was successful, False otherwise
        """
        if quantity <= 0 or symbol not in self.portfolio or self.portfolio[symbol] < quantity:
            return False
        
        try:
            price = get_share_price(symbol)
            total_value = price * quantity
            
            # Update balance
            self.balance += total_value
            
            # Update portfolio
            self.portfolio[symbol] -= quantity
            
            # If no shares left, remove from portfolio
            if self.portfolio[symbol] == 0:
                del self.portfolio[symbol]
            
            # Record the transaction
            transaction = {
                'type': TransactionType.SELL,
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'total': total_value,
                'timestamp': datetime.now(),
                'details': f"Sold {quantity} shares of {symbol} at ${price:.2f} each, total: ${total_value:.2f}"
            }
            self.transactions.append(transaction)
            
            return True
            
        except ValueError as e:
            # Handle case where symbol is invalid
            return False
    
    def get_portfolio_value(self):
        """
        Calculate the total value of the portfolio.
        
        Returns:
            float: The total value of all shares in the portfolio
        """
        total_value = 0.0
        
        for symbol, quantity in self.portfolio.items():
            try:
                price = get_share_price(symbol)
                total_value += price * quantity
            except ValueError:
                # Skip symbols with no price information
                pass
        
        return total_value
    
    def get_profit_or_loss(self):
        """
        Calculate the profit or loss since the initial deposit.
        
        Returns:
            float: The profit (positive) or loss (negative)
        """
        current_value = self.balance + self.get_portfolio_value()
        return current_value - self.initial_deposit
    
    def get_holdings(self):
        """
        Get the current holdings.
        
        Returns:
            dict: A dictionary of stock symbols and their quantities
        """
        return self.portfolio.copy()
    
    def list_transactions(self):
        """
        List all transactions.
        
        Returns:
            list: A list of all transactions
        """
        return [transaction['details'] for transaction in self.transactions]