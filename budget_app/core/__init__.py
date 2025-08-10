"""
Core functionality for the budget application.

This module contains the core business logic, database models,
and data processing functionality.
"""

from .models import Transaction, Base
from .database import (
    get_db,
    import_transactions_from_csv,
    get_transactions,
    get_categories,
    get_aggregated_expenses,
    delete_transaction,
    DatabaseError,
    DuplicateEntryError,
    ValidationError,
)

__all__ = [
    'Transaction',
    'Base',
    'get_db',
    'import_transactions_from_csv',
    'get_transactions',
    'get_categories',
    'get_aggregated_expenses',
    'delete_transaction',
    'DatabaseError',
    'DuplicateEntryError',
    'ValidationError',
]
