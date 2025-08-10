
from datetime import datetime

class Expense:

    def __init__(self, name, category, amount, transaction_date=None) -> None:
        self.name = name
        self.category = category
        self.amount = amount
        if transaction_date:
            self.transaction_date = transaction_date
        else:
            self.transaction_date = datetime.now().strftime('%Y-%m-%d')  # Default to current date

    def __repr__(self):
        return f"<Expense: {self.name}, {self.category}, ${self.amount:.2f}, Date: {self.transaction_date} >"