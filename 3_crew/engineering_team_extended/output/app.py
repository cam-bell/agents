import gradio as gr
import pandas as pd
from accounts import Account, get_share_price

# Initialize an account for our demo user
account = Account("demo_user")

def create_account(initial_deposit):
    """Create account with initial deposit"""
    if account.balance > 0 or account.transactions:
        return "Account already exists and has been initialized"
    
    success = account.deposit(float(initial_deposit))
    if success:
        return f"Account created successfully with ${float(initial_deposit):.2f}"
    else:
        return "Failed to create account. Deposit amount must be positive."

def deposit_funds(amount):
    """Deposit funds to the account"""
    success = account.deposit(float(amount))
    if success:
        return f"Successfully deposited ${float(amount):.2f}"
    else:
        return "Deposit failed. Amount must be positive."

def withdraw_funds(amount):
    """Withdraw funds from the account"""
    success = account.withdraw(float(amount))
    if success:
        return f"Successfully withdrew ${float(amount):.2f}"
    else:
        return "Withdrawal failed. Amount must be positive and less than your balance."

def buy_stock(symbol, quantity):
    """Buy shares of a stock"""
    try:
        quantity = int(quantity)
        success = account.buy_shares(symbol, quantity)
        if success:
            price = get_share_price(symbol)
            return f"Successfully bought {quantity} shares of {symbol} at ${price:.2f} each"
        else:
            return "Purchase failed. Check that you have sufficient funds and valid inputs."
    except ValueError:
        return "Invalid input. Please check the stock symbol and quantity."

def sell_stock(symbol, quantity):
    """Sell shares of a stock"""
    try:
        quantity = int(quantity)
        success = account.sell_shares(symbol, quantity)
        if success:
            price = get_share_price(symbol)
            return f"Successfully sold {quantity} shares of {symbol} at ${price:.2f} each"
        else:
            return "Sale failed. Check that you own sufficient shares and provided valid inputs."
    except ValueError:
        return "Invalid input. Please check the stock symbol and quantity."

def get_account_summary():
    """Get a summary of the account status"""
    balance = account.balance
    portfolio_value = account.get_portfolio_value()
    total_value = balance + portfolio_value
    profit_loss = account.get_profit_or_loss()
    
    summary = f"""
    Current Cash Balance: ${balance:.2f}
    Portfolio Value: ${portfolio_value:.2f}
    Total Value: ${total_value:.2f}
    Profit/Loss: ${profit_loss:.2f} ({'profit' if profit_loss >= 0 else 'loss'})
    """
    return summary

def get_portfolio():
    """Get the current portfolio holdings"""
    holdings = account.get_holdings()
    
    if not holdings:
        return "No holdings in portfolio"
    
    result = "Current Portfolio:\n"
    total_value = 0.0
    
    for symbol, quantity in holdings.items():
        price = get_share_price(symbol)
        value = price * quantity
        total_value += value
        result += f"{symbol}: {quantity} shares at ${price:.2f} each = ${value:.2f}\n"
    
    result += f"\nTotal Portfolio Value: ${total_value:.2f}"
    return result

def get_transaction_history():
    """Get the transaction history"""
    transactions = account.list_transactions()
    
    if not transactions:
        return "No transactions recorded"
    
    result = "Transaction History:\n\n"
    for i, transaction in enumerate(transactions, 1):
        result += f"{i}. {transaction}\n"
    
    return result

def get_available_stocks():
    """Get a list of available stocks for testing"""
    return "Available test stocks: AAPL ($150.00), TSLA ($800.00), GOOGL ($2500.00)"

# Create the Gradio interface
with gr.Blocks(title="Trading Account Simulator") as demo:
    gr.Markdown("# Trading Account Simulator")
    gr.Markdown("A simple interface to manage a trading account")
    
    with gr.Tab("Account Setup"):
        gr.Markdown("## Create Account")
        with gr.Row():
            initial_deposit = gr.Number(label="Initial Deposit ($)")
            create_btn = gr.Button("Create Account")
        create_output = gr.Textbox(label="Result")
        create_btn.click(create_account, inputs=initial_deposit, outputs=create_output)
        
        gr.Markdown("## Account Management")
        with gr.Row():
            deposit_amount = gr.Number(label="Deposit Amount ($)")
            deposit_btn = gr.Button("Deposit")
        deposit_output = gr.Textbox(label="Result")
        deposit_btn.click(deposit_funds, inputs=deposit_amount, outputs=deposit_output)
        
        with gr.Row():
            withdraw_amount = gr.Number(label="Withdraw Amount ($)")
            withdraw_btn = gr.Button("Withdraw")
        withdraw_output = gr.Textbox(label="Result")
        withdraw_btn.click(withdraw_funds, inputs=withdraw_amount, outputs=withdraw_output)
    
    with gr.Tab("Trading"):
        gr.Markdown("## Buy & Sell Stocks")
        available_stocks = gr.Textbox(label="Available Stocks", value=get_available_stocks())
        
        with gr.Row():
            buy_symbol = gr.Textbox(label="Stock Symbol")
            buy_quantity = gr.Number(label="Quantity", precision=0)
            buy_btn = gr.Button("Buy")
        buy_output = gr.Textbox(label="Result")
        buy_btn.click(buy_stock, inputs=[buy_symbol, buy_quantity], outputs=buy_output)
        
        with gr.Row():
            sell_symbol = gr.Textbox(label="Stock Symbol")
            sell_quantity = gr.Number(label="Quantity", precision=0)
            sell_btn = gr.Button("Sell")
        sell_output = gr.Textbox(label="Result")
        sell_btn.click(sell_stock, inputs=[sell_symbol, sell_quantity], outputs=sell_output)
    
    with gr.Tab("Portfolio & History"):
        gr.Markdown("## Account Summary")
        summary_btn = gr.Button("Get Account Summary")
        summary_output = gr.Textbox(label="Account Summary")
        summary_btn.click(get_account_summary, inputs=None, outputs=summary_output)
        
        gr.Markdown("## Portfolio Holdings")
        portfolio_btn = gr.Button("View Portfolio")
        portfolio_output = gr.Textbox(label="Portfolio")
        portfolio_btn.click(get_portfolio, inputs=None, outputs=portfolio_output)
        
        gr.Markdown("## Transaction History")
        history_btn = gr.Button("View Transactions")
        history_output = gr.Textbox(label="Transactions")
        history_btn.click(get_transaction_history, inputs=None, outputs=history_output)

# Launch the app
if __name__ == "__main__":
    demo.launch()