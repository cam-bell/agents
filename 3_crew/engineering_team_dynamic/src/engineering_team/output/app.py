import gradio as gr
from user_account import UserAccount
from transaction_manager import TransactionManager
from share_price_service import SharePriceService
from portfolio_manager import PortfolioManager
from reporting_manager import ReportingManager

# Initialize objects
initial_deposit = 1000.0
user_account = UserAccount('user_123', initial_deposit)
share_price_service = SharePriceService()
transaction_manager = TransactionManager(user_account)
portfolio_manager = PortfolioManager(transaction_manager, share_price_service)
reporting_manager = ReportingManager(user_account, portfolio_manager, transaction_manager)

def create_account(user_id, deposit_amount):
    global user_account, transaction_manager, portfolio_manager, reporting_manager
    user_account = UserAccount(user_id, deposit_amount)
    transaction_manager = TransactionManager(user_account)
    portfolio_manager = PortfolioManager(transaction_manager, share_price_service)
    reporting_manager = ReportingManager(user_account, portfolio_manager, transaction_manager)
    return "Account created successfully."

def deposit_funds(amount):
    if user_account.deposit(amount):
        return f"Deposited: ${amount}. Current Balance: ${user_account.get_balance()}"
    return "Invalid deposit amount."

def withdraw_funds(amount):
    if user_account.withdraw(amount):
        return f"Withdrawn: ${amount}. Current Balance: ${user_account.get_balance()}"
    return "Invalid withdrawal amount or insufficient funds."

def buy_shares(symbol, quantity):
    price = share_price_service.get_share_price(symbol)
    if transaction_manager.buy_shares(symbol, int(quantity), price):
        return f"Bought {quantity} shares of {symbol} at ${price} each."
    return "Insufficient funds or invalid transaction."

def sell_shares(symbol, quantity):
    price = share_price_service.get_share_price(symbol)
    if transaction_manager.sell_shares(symbol, int(quantity), price):
        return f"Sold {quantity} shares of {symbol} at ${price} each."
    return "Insufficient holdings or invalid transaction."

def get_holdings():
    return reporting_manager.generate_holdings_report()

def get_transactions():
    return reporting_manager.generate_transaction_report()

def get_financial_report():
    report = reporting_manager.generate_financial_report(initial_deposit)
    return report

with gr.Blocks() as demo:
    with gr.Tab("Account Management"):
        user_id = gr.Textbox(label="User ID")
        deposit_amount = gr.Number(label="Initial Deposit", value=initial_deposit)
        create_btn = gr.Button("Create Account")
        create_btn.click(create_account, inputs=[user_id, deposit_amount], outputs="text")
        
        deposit_input = gr.Number(label="Deposit Amount")
        deposit_btn = gr.Button("Deposit Funds")
        deposit_output = gr.Textbox(label="Response")
        deposit_btn.click(deposit_funds, inputs=deposit_input, outputs=deposit_output)
        
        withdraw_input = gr.Number(label="Withdraw Amount")
        withdraw_btn = gr.Button("Withdraw Funds")
        withdraw_output = gr.Textbox(label="Response")
        withdraw_btn.click(withdraw_funds, inputs=withdraw_input, outputs=withdraw_output)

    with gr.Tab("Trading"):
        symbol = gr.Textbox(label="Share Symbol")
        quantity = gr.Number(label="Quantity")
        buy_btn = gr.Button("Buy Shares")
        buy_output = gr.Textbox(label="Response")
        buy_btn.click(buy_shares, inputs=[symbol, quantity], outputs=buy_output)
        
        sell_btn = gr.Button("Sell Shares")
        sell_output = gr.Textbox(label="Response")
        sell_btn.click(sell_shares, inputs=[symbol, quantity], outputs=sell_output)
    
    with gr.Tab("Reports"):
        holdings_btn = gr.Button("Get Holdings")
        holdings_output = gr.JSON(label="Holdings")
        holdings_btn.click(get_holdings, outputs=holdings_output)

        transactions_btn = gr.Button("Get Transactions")
        transactions_output = gr.JSON(label="Transactions")
        transactions_btn.click(get_transactions, outputs=transactions_output)

        financial_btn = gr.Button("Get Financial Report")
        financial_output = gr.JSON(label="Financial Report")
        financial_btn.click(get_financial_report, outputs=financial_output)

if __name__ == "__main__":
    demo.launch()