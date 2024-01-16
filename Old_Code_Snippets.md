##  Went after "amount_by_category = {} " function
    
```
print("Expenses by Category 📊:")
    for key, amount in amount_by_category.items():
        print(f"  {key}: ${amount:.2f}")
        if budget_tracker.is_within_budget(key, amount):
            print(f"✅ Within budget for {key}")
        else:
            print(f"⚠️ Over budget for {key}")

    total_spent = sum([ex.amount for ex in expenses])
    print(f"💵 Total Spent ${total_spent:.2f} this month")

    remaining_budget = budget - total_spent
    print(f"✅ Budget Remaining ${remaining_budget:.2f} this month")

    # Get the current date
    current_date = datetime.now()

    # Get the current year and month
    current_year = current_date.year
    current_month = current_date.month

       # Find the number of days in the specified month
    _, last_day_of_month = calendar.monthrange(year, month)

    # Calculate the remaining days (assuming analysis is done at the end of the month)
    remaining_days = last_day_of_month

    # Calculate the number of weeks left
    weeks_left = (remaining_days + 6) // 7

    # Calculate money left to use per week
    total_money_left = remaining_budget
    money_per_week = total_money_left / weeks_left if weeks_left > 0 else 0

    print(f"Weeks left in {month}/{year}: {weeks_left}")
    print(green(f"Money left to use per week: ${money_per_week:.2f}"))
```