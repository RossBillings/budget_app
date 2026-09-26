"""
Core functionality for the budget application.

This module contains the core business logic, database models,
and data processing functionality.
"""

from .models import Transaction, Base
from .categorizer import CategoryRules, load_category_rules
from .database import (
    get_db,
    import_transactions_from_csv,
    recategorize_transactions,
    get_transactions,
    get_categories,
    get_aggregated_expenses,
    get_category_monthly_totals,
    delete_transaction,
    DatabaseError,
    DuplicateEntryError,
    ValidationError,
)

__all__ = [
    'Transaction',
    'Base',
    'CategoryRules',
    'load_category_rules',
    'get_db',
    'import_transactions_from_csv',
    'recategorize_transactions',
    'get_transactions',
    'get_categories',
    'get_aggregated_expenses',
    'get_category_monthly_totals',
    'delete_transaction',
    'DatabaseError',
    'DuplicateEntryError',
    'ValidationError',
]
