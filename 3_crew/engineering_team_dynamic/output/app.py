import gradio as gr
from accounts import Account, get_share_price

# Initialize account for demo
account = None

def create_new_account(user_id, initial_deposit):
    global account
    try:
        account = Account(user_id, float(initial_deposit))
        return f"Account created for {user_id} with initial deposit of ${initial_deposit}"
    except ValueError as e:
        return f"Error: {str(e)}"

def deposit(amount):
    global account
    if account is None:
        return "Please create an account first."
    try:
        new_balance = account.deposit_funds(float(amount))
        return f"Successfully deposited ${amount}. New balance: ${new_balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def withdraw(amount):
    global account
    if account is None:
        return "Please create an account first."
    try:
        new_balance = account.withdraw_funds(float(amount))
        return f"Successfully withdrew ${amount}. New balance: ${new_balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def buy_stock(symbol, quantity):
    global account
    if account is None:
        return "Please create an account first."
    try:
        shares_owned = account.buy_shares(symbol, int(quantity))
        return f"Successfully bought {quantity} shares of {symbol}. You now own {shares_owned} shares."
    except ValueError as e:
        return f"Error: {str(e)}"

def sell_stock(symbol, quantity):
    global account
    if account is None:
        return "Please create an account first."
    try:
        shares_owned = account.sell_shares(symbol, int(quantity))
        return f"Successfully sold {quantity} shares of {symbol}. You now own {shares_owned} shares."
    except ValueError as e:
        return f"Error: {str(e)}"

def get_portfolio_value():
    global account
    if account is None:
        return "Please create an account first."
    
    portfolio_value = account.calculate_portfolio_value()
    return f"Current portfolio value: ${portfolio_value:.2f}"

def get_profit_loss():
    global account
    if account is None:
        return "Please create an account first."
    
    profit_loss_data = account.report_profit_or_loss()
    profit_loss = profit_loss_data["profit_or_loss"]
    percent = profit_loss_data["profit_or_loss_percentage"]
    
    return f"Initial deposit: ${profit_loss_data['initial_deposit']:.2f}\nCurrent value: ${profit_loss_data['current_value']:.2f}\nProfit/Loss: ${profit_loss:.2f} ({percent:.2f}%)"

def get_holdings():
    global account
    if account is None:
        return "Please create an account first."
    
    holdings_data = account.report_holdings()
    result = f"Cash balance: ${holdings_data['cash_balance']:.2f}\n\nShares:\n"
    
    for symbol, data in holdings_data["shares"].items():
        result += f"{symbol}: {data['quantity']} shares @ ${data['current_price']:.2f} = ${data['current_value']:.2f}\n"
    
    result += f"\nTotal portfolio value: ${holdings_data['total_value']:.2f}"
    return result

def get_transactions():
    global account
    if account is None:
        return "Please create an account first."
    
    transactions = account.list_transactions()
    if not transactions:
        return "No transactions yet."
    
    result = "Transaction History:\n"
    for i, tx in enumerate(transactions, 1):
        result += f"\n{i}. Type: {tx['type']}"
        
        if tx['type'] == "DEPOSIT" or tx['type'] == "WITHDRAWAL":
            result += f", Amount: ${tx['amount']:.2f}"
        elif tx['type'] == "BUY":
            result += f", Symbol: {tx['symbol']}, Quantity: {tx['quantity']}, Price: ${tx['price']:.2f}, Total: ${tx['total_cost']:.2f}"
        elif tx['type'] == "SELL":
            result += f", Symbol: {tx['symbol']}, Quantity: {tx['quantity']}, Price: ${tx['price']:.2f}, Total: ${tx['total_value']:.2f}"
        
        result += f", Balance after: ${tx['balance_after']:.2f}"
    
    return result

def get_available_stocks():
    return "Available stocks for demo: AAPL ($150.25), TSLA ($820.75), GOOGL ($2750.50)"

with gr.Blocks(title="Trading Simulator") as demo:
    gr.Markdown("# Trading Simulation Platform")
    gr.Markdown("This is a simple demo of the trading simulation platform.")
    
    with gr.Tab("Account Management"):
        with gr.Group():
            gr.Markdown("### Create Account")
            with gr.Row():
                user_id_input = gr.Textbox(label="User ID", placeholder="Enter your user ID")
                initial_deposit = gr.Number(label="Initial Deposit", value=1000.0)
            create_btn = gr.Button("Create Account")
            create_output = gr.Textbox(label="Result")
            create_btn.click(create_new_account, [user_id_input, initial_deposit], create_output)
        
        with gr.Group():
            gr.Markdown("### Deposit/Withdraw Funds")
            with gr.Row():
                deposit_amount = gr.Number(label="Amount", value=100.0)
                deposit_btn = gr.Button("Deposit")
                withdraw_btn = gr.Button("Withdraw")
            fund_output = gr.Textbox(label="Result")
            deposit_btn.click(deposit, [deposit_amount], fund_output)
            withdraw_btn.click(withdraw, [deposit_amount], fund_output)
    
    with gr.Tab("Trading"):
        gr.Markdown("### Buy/Sell Stocks")
        stocks_info = gr.Textbox(label="Available Stocks", value=get_available_stocks())
        
        with gr.Row():
            symbol_input = gr.Textbox(label="Stock Symbol", placeholder="e.g. AAPL")
            quantity_input = gr.Number(label="Quantity", value=1, precision=0)
        
        with gr.Row():
            buy_btn = gr.Button("Buy")
            sell_btn = gr.Button("Sell")
        
        trading_output = gr.Textbox(label="Result")
        buy_btn.click(buy_stock, [symbol_input, quantity_input], trading_output)
        sell_btn.click(sell_stock, [symbol_input, quantity_input], trading_output)
    
    with gr.Tab("Portfolio"):
        gr.Markdown("### Portfolio Information")
        
        with gr.Row():
            portfolio_btn = gr.Button("Get Portfolio Value")
            holdings_btn = gr.Button("View Holdings")
            profit_loss_btn = gr.Button("Check Profit/Loss")
            transactions_btn = gr.Button("View Transactions")
        
        portfolio_output = gr.Textbox(label="Result", lines=10)
        
        portfolio_btn.click(get_portfolio_value, [], portfolio_output)
        holdings_btn.click(get_holdings, [], portfolio_output)
        profit_loss_btn.click(get_profit_loss, [], portfolio_output)
        transactions_btn.click(get_transactions, [], portfolio_output)

if __name__ == "__main__":
    demo.launch()