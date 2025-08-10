import csv

class BudgetADV:
    def __init__(self):
        self.category_budgets = {}

    def load_budgets_from_csv(self, file_path):
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                category, amount = row
                self.category_budgets[category] = float(amount)

    def set_budget(self, category, amount):
        self.category_budgets[category] = amount

    def is_within_budget(self, category, spent_amount):
        budget_amount = self.category_budgets.get(category, 0)
        return spent_amount <= budget_amount
    
    def get_total_budget(self):
        return sum(self.category_budgets.values())

