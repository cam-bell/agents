import unittest
from accounts import Account, get_share_price

class TestAccount(unittest.TestCase):

    def setUp(self):
        self.account = Account()

    def test_initial_state(self):
        self.assertEqual(self.account.balance, 0.0)
        self.assertEqual(self.account.initial_deposit, 0.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(self.account.transactions, [])

    def test_deposit_funds(self):
        self.account.deposit_funds(100)
        self.assertEqual(self.account.balance, 100)
        self.assertEqual(self.account.initial_deposit, 100)
        self.assertIn(('DEPOSIT', 100), self.account.transactions)

        with self.assertRaises(ValueError):
            self.account.deposit_funds(-50)

    def test_withdraw_funds(self):
        self.account.deposit_funds(100)
        self.account.withdraw_funds(50)
        self.assertEqual(self.account.balance, 50)
        self.assertIn(('WITHDRAW', 50), self.account.transactions)

        with self.assertRaises(ValueError):
            self.account.withdraw_funds(60)

        with self.assertRaises(ValueError):
            self.account.withdraw_funds(-10)

    def test_record_transaction(self):
        self.account.deposit_funds(1000)
        self.account.record_transaction('AAPL', 2)
        price = get_share_price('AAPL')
        self.assertEqual(self.account.balance, 1000 - price * 2)
        self.assertEqual(self.account.holdings['AAPL'], 2)
        self.assertIn(('BUY', 'AAPL', 2, price), self.account.transactions)

        with self.assertRaises(ValueError):
            self.account.record_transaction('AAPL', 1000)

        with self.assertRaises(ValueError):
            self.account.record_transaction('AAPL', -3)

    def test_calculate_portfolio_value(self):
        self.account.deposit_funds(2000)
        self.account.record_transaction('AAPL', 5)
        self.account.record_transaction('TSLA', 1)
        expected_value = get_share_price('AAPL') * 5 + get_share_price('TSLA')
        self.assertEqual(self.account.calculate_portfolio_value(), expected_value)

    def test_calculate_profit_loss(self):
        self.account.deposit_funds(1500)
        self.account.record_transaction('GOOGL', 1)
        self.account.record_transaction('AAPL', 2)
        portfolio_value = self.account.calculate_portfolio_value()
        expected_profit_loss = portfolio_value + self.account.balance - self.account.initial_deposit
        self.assertEqual(self.account.calculate_profit_loss(), expected_profit_loss)

    def test_report_holdings(self):
        self.account.deposit_funds(300)
        self.account.record_transaction('GOOGL', 1)
        self.assertEqual(self.account.report_holdings(), {'GOOGL': 1})

    def test_report_profit_loss(self):
        self.account.deposit_funds(700)
        self.account.record_transaction('TSLA', 1)
        expected_profit_loss = self.account.calculate_profit_loss()
        self.assertEqual(self.account.report_profit_loss(), expected_profit_loss)

    def test_list_transactions(self):
        self.account.deposit_funds(400)
        self.account.withdraw_funds(100)
        self.account.record_transaction('AAPL', 1)
        expected_transactions = [('DEPOSIT', 400), ('WITHDRAW', 100), ('BUY', 'AAPL', 1, get_share_price('AAPL'))]
        self.assertEqual(self.account.list_transactions(), expected_transactions)

if __name__ == '__main__':
    unittest.main()