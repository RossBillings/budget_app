"""
Database session management and core operations for the budget application.

This module provides:
- Session management with context managers
- Core database operations (CRUD)
- Bulk import functionality with deduplication
- Query helpers for common operations
"""
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
import logging

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import SessionLocal, Transaction, Base, engine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class DuplicateEntryError(DatabaseError):
    """Raised when a duplicate entry is detected."""
    pass


class ValidationError(DatabaseError):
    """Raised when data validation fails."""
    pass


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Provides a session that automatically handles commits and rollbacks.
    The session is automatically closed when the context exits.
    
    Yields:
        Session: A new database session
        
    Example:
        with get_db() as db:
            result = db.query(Transaction).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: transactions.dedupe_key" in str(e):
            raise DuplicateEntryError("Duplicate transaction detected") from e
        raise DatabaseError(f"Database integrity error: {e}") from e
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise DatabaseError(f"Database operation failed: {e}") from e
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in database session: {e}")
        raise
    finally:
        db.close()

def import_transactions_from_csv(
    file_path: str,
    default_category: str = "misc",
    source: str = "csv",
    batch_size: int = 1000,
    auto_categorize: bool = True,
) -> Dict[str, int]:
    """
    Import transactions from a CSV file into the database with deduplication.
    
    Args:
        file_path: Path to the CSV file
        default_category: Default category if not specified in CSV
        source: Source identifier for the transactions
        batch_size: Number of records to process in each batch
        
    Returns:
        Dict with counts of inserted, skipped, and duplicate transactions
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        DatabaseError: For database-related errors
    """
    import csv
    from pathlib import Path
    
    if not Path(file_path).is_file():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    result = {"inserted": 0, "skipped": 0, "duplicates": 0, "errors": 0}
    
    with get_db() as db, open(file_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        batch = []
        
        for row_num, row in enumerate(reader, 1):
            try:
                # Preprocess the CSV row to standardize format
                processed_row = _preprocess_csv_row(row)
                
                # Skip excluded transactions
                if _should_exclude_transaction(processed_row.get("Description", "")):
                    continue
                
                # Create transaction from CSV row
                txn = Transaction.from_csv_row(processed_row, default_category=default_category, auto_categorize=auto_categorize)
                txn.source = source
                batch.append(txn)
                
                # Process batch when it reaches the specified size
                if len(batch) >= batch_size:
                    batch_result = _process_batch(db, batch)
                    _update_result(result, batch_result)
                    batch = []
                    
            except ValueError as e:
                logger.warning(f"Skipping invalid row {row_num}: {e}")
                result["skipped"] += 1
            except Exception as e:
                logger.error(f"Error processing row {row_num}: {e}")
                result["errors"] += 1
        
        # Process any remaining records in the final batch
        if batch:
            batch_result = _process_batch(db, batch)
            _update_result(result, batch_result)
    
    logger.info(
        f"Import complete. Inserted: {result['inserted']}, "
        f"Duplicates: {result['duplicates']}, "
        f"Skipped: {result['skipped']}, "
        f"Errors: {result['errors']}"
    )
    return result


def _preprocess_csv_row(row: Dict[str, str]) -> Dict[str, str]:
    """
    Preprocess a CSV row to standardize format between Capital One and USAA.
    
    Args:
        row: Raw CSV row dictionary
        
    Returns:
        Dict with standardized keys: Transaction Date, Description, Amount
    """
    processed_row = {}
    
    # Handle Capital One format (has Debit/Credit columns)
    if 'Debit' in row and 'Credit' in row:
        # Use debit amount or negative credit amount
        debit = row.get('Debit', '').strip()
        credit = row.get('Credit', '').strip()
        
        if debit:
            processed_row['Amount'] = debit
        elif credit:
            processed_row['Amount'] = f"-{credit}"
        else:
            processed_row['Amount'] = "0"
            
        processed_row['Transaction Date'] = row.get('Transaction Date', '').strip()
        processed_row['Description'] = row.get('Description', '').strip()
    
    # Handle USAA format (has single Amount column)
    elif 'Amount' in row:
        try:
            amount_val = float(row['Amount'])
            # Invert the sign for USAA input (their format is opposite)
            amount_val = -amount_val
            processed_row['Amount'] = str(amount_val)
        except ValueError:
            processed_row['Amount'] = row['Amount']
            
        processed_row['Transaction Date'] = row.get('Date', '').strip()
        processed_row['Description'] = row.get('Description', '').strip()
    
    # Handle already processed format
    else:
        processed_row['Transaction Date'] = row.get('Transaction Date', '').strip()
        processed_row['Description'] = row.get('Description', '').strip()
        processed_row['Amount'] = row.get('Amount', '0').strip()
    
    return processed_row


def _should_exclude_transaction(description: str) -> bool:
    """
    Check if a transaction should be excluded from import.
    
    Args:
        description: Transaction description
        
    Returns:
        bool: True if transaction should be excluded
    """
    from .categorization import should_exclude
    return should_exclude(description)


def _process_batch(db: Session, batch: List[Transaction]) -> Dict[str, int]:
    """Process a batch of transactions with deduplication."""
    if not batch:
        return {"inserted": 0, "duplicates": 0, "errors": 0}
    
    result = {"inserted": 0, "duplicates": 0, "errors": 0}
    
    try:
        # Get existing dedupe keys to avoid constraint violations
        dedupe_keys = {txn.dedupe_key for txn in batch}
        existing_keys = set(
            db.query(Transaction.dedupe_key)
            .filter(Transaction.dedupe_key.in_(dedupe_keys))
            .all()
        )
        
        # Remove duplicates within the batch itself
        seen_keys = set()
        unique_transactions = []
        batch_duplicates = 0
        
        for txn in batch:
            if txn.dedupe_key in seen_keys:
                batch_duplicates += 1
                continue
            seen_keys.add(txn.dedupe_key)
            unique_transactions.append(txn)
        
        # Filter out existing database duplicates
        new_transactions = [
            txn for txn in unique_transactions 
            if txn.dedupe_key not in existing_keys
        ]
        
        # Insert new transactions
        if new_transactions:
            db.bulk_save_objects(new_transactions)
            result["inserted"] = len(new_transactions)
        
        result["duplicates"] = batch_duplicates + (len(unique_transactions) - len(new_transactions))
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing batch: {e}")
        result["errors"] = len(batch)
    
    return result


def _update_result(total: Dict[str, int], batch: Dict[str, int]) -> None:
    """Update the total result with batch results."""
    for key in total:
        total[key] += batch.get(key, 0)

def get_aggregated_expenses(
    category: str,
    start_date: Optional[Union[date, str]] = None,
    end_date: Optional[Union[date, str]] = None
) -> List[Dict[str, Any]]:
    """
    Get aggregated expenses by month for a specific category.
    
    Args:
        category: Category to filter by (case-insensitive)
        start_date: Optional start date filter (inclusive). Can be date object or 'YYYY-MM-DD' string.
        end_date: Optional end date filter (inclusive). Can be date object or 'YYYY-MM-DD' string.
        
    Returns:
        List of dicts with 'month' and 'total' keys, sorted by month
        
    Example:
        # Get all expenses in 'food' category for 2023
        expenses = get_aggregated_expenses(
            category='food',
            start_date='2023-01-01',
            end_date='2023-12-31'
        )
    """
    # Convert string dates to date objects if needed
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    with get_db() as db:
        query = db.query(
            func.strftime('%Y-%m', Transaction.transaction_date).label('month'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            func.lower(Transaction.category) == category.lower()
        )
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        # Execute query and return results
        results = query.group_by('month').order_by('month').all()
        
        # Convert results to list of dicts for better JSON serialization
        return [
            {"month": month, "total": float(total) if total else 0.0}
            for month, total in results
        ]

def get_transactions(
    category: str,
    keyword: Optional[str] = None,
    start_date: Optional[Union[date, str]] = None,
    end_date: Optional[Union[date, str]] = None,
    sort_by: str = "date",
    order: str = "asc",
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Tuple[List[Transaction], int]:
    """
    Get filtered, sorted, and paginated transactions.
    
    Args:
        category: Category to filter by (case-insensitive)
        keyword: Optional keyword to search in description (case-insensitive)
        start_date: Optional start date filter (inclusive). Can be date object or 'YYYY-MM-DD' string.
        end_date: Optional end date filter (inclusive). Can be date object or 'YYYY-MM-DD' string.
        sort_by: Field to sort by ('date' or 'amount')
        order: Sort order ('asc' or 'desc')
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        Tuple of (list of Transaction objects, total count of matching records)
        
    Example:
        # Get first 10 food transactions in 2023, sorted by amount descending
        transactions, total = get_transactions(
            category='food',
            start_date='2023-01-01',
            end_date='2023-12-31',
            sort_by='amount',
            order='desc',
            limit=10,
            offset=0
        )
    """
    # Convert string dates to date objects if needed
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    db = SessionLocal()
    try:
        # Build base query
        query = db.query(Transaction)
        
        # Apply category filter if provided
        if category:
            query = query.filter(
                func.lower(Transaction.category) == category.lower()
            )
        
        # Apply filters
        if keyword:
            query = query.filter(
                func.lower(Transaction.description).contains(keyword.lower())
            )
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        order_column = {
            'date': Transaction.transaction_date,
            'amount': Transaction.amount,
            'description': Transaction.description
        }.get(sort_by.lower(), Transaction.transaction_date)
        
        if order.lower() == 'desc':
            order_column = order_column.desc()
        else:
            order_column = order_column.asc()
        
        # Apply sorting first, then pagination
        query = query.order_by(order_column)
        
        # Apply pagination
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        
        # Execute query and detach objects from session
        transactions = query.all()
        
        # Detach objects from session to avoid DetachedInstanceError
        for txn in transactions:
            db.refresh(txn)
            db.expunge(txn)
        
        return transactions, total
    finally:
        db.close()


def get_categories() -> List[Dict[str, Any]]:
    """
    Get list of all categories with their total amounts.
    
    Returns:
        List of dicts with 'category' and 'total' keys, sorted by total descending
    """
    with get_db() as db:
        results = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).group_by(
            Transaction.category
        ).order_by(
            func.sum(Transaction.amount).desc()
        ).all()
        
        return [
            {"category": category, "total": float(total) if total else 0.0}
            for category, total in results
        ]


def get_transaction_years() -> List[int]:
    """
    Get list of years for which transaction data exists.
    
    Returns:
        List of distinct years, sorted in ascending order
    """
    with get_db() as db:
        results = db.query(
            func.strftime('%Y', Transaction.transaction_date).label('year')
        ).distinct().order_by('year').all()
        
        return [int(year) for year, in results]


def delete_transaction(transaction_id: str) -> bool:
    """
    Delete a transaction by ID.
    
    Args:
        transaction_id: ID of the transaction to delete
        
    Returns:
        bool: True if the transaction was deleted, False if not found
    """
    with get_db() as db:
        rows_deleted = db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).delete()
        
        if rows_deleted > 0:
            db.commit()
            return True
        return False


def get_aggregated_expenses_by_month(
    category: Optional[str] = None,
    start_date: Optional[Union[date, str]] = None,
    end_date: Optional[Union[date, str]] = None
) -> List[Dict[str, Any]]:
    """
    Get aggregated expenses grouped by month.
    
    Args:
        category: Optional category filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of dictionaries with month and total amount
    """
    with get_db() as db:
        query = db.query(
            func.strftime('%Y-%m', Transaction.transaction_date).label('month'),
            func.sum(Transaction.amount).label('total')
        )
        
        # Apply filters
        if category and category != 'all':
            query = query.filter(Transaction.category == category)
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.transaction_date <= end_date)
        
        # Group by month and order by month
        query = query.group_by(func.strftime('%Y-%m', Transaction.transaction_date))
        query = query.order_by(func.strftime('%Y-%m', Transaction.transaction_date))
        
        results = query.all()
        
        return [
            {
                'month': result.month,
                'total': float(result.total) if result.total else 0.0
            }
            for result in results
        ]


def get_spending_patterns(
    start_date: Optional[Union[date, str]] = None,
    end_date: Optional[Union[date, str]] = None
) -> Dict[str, Any]:
    """
    Get spending patterns analysis.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Dictionary with spending pattern data
    """
    with get_db() as db:
        # Base query
        base_query = db.query(Transaction)
        
        # Apply date filters
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            base_query = base_query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            base_query = base_query.filter(Transaction.transaction_date <= end_date)
        
        # Day of week analysis
        day_of_week_query = base_query.with_entities(
            func.strftime('%w', Transaction.transaction_date).label('day_of_week'),
            func.sum(Transaction.amount).label('total')
        ).group_by(func.strftime('%w', Transaction.transaction_date))
        
        day_results = day_of_week_query.all()
        day_patterns = [0] * 7  # Initialize array for 7 days
        for result in day_results:
            day_index = int(result.day_of_week)
            day_patterns[day_index] = float(result.total) if result.total else 0.0
        
        # Time of day analysis (using transaction ID as proxy for time)
        # This is a simplified approach - in a real app you'd have actual timestamps
        time_patterns = [0] * 24  # Initialize array for 24 hours
        
        return {
            'day_of_week': day_patterns,
            'time_of_day': time_patterns
        }


def get_monthly_comparison(
    start_date: Optional[Union[date, str]] = None,
    end_date: Optional[Union[date, str]] = None
) -> Dict[str, Any]:
    """
    Get monthly comparison data.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Dictionary with current and previous month data
    """
    with get_db() as db:
        # Get current month data
        current_month_query = db.query(
            func.sum(Transaction.amount).label('total')
        ).filter(
            func.strftime('%Y-%m', Transaction.transaction_date) == 
            func.strftime('%Y-%m', 'now')
        )
        
        # Get previous month data
        previous_month_query = db.query(
            func.sum(Transaction.amount).label('total')
        ).filter(
            func.strftime('%Y-%m', Transaction.transaction_date) == 
            func.strftime('%Y-%m', 'now', '-1 month')
        )
        
        current_total = current_month_query.scalar() or 0.0
        previous_total = previous_month_query.scalar() or 0.0
        
        return {
            'current_month': float(current_total),
            'previous_month': float(previous_total),
            'change_percentage': ((current_total - previous_total) / previous_total * 100) if previous_total != 0 else 0
        }


def get_aggregated_expenses(
    category: Optional[str] = None,
    start_date: Optional[Union[date, str]] = None,
    end_date: Optional[Union[date, str]] = None
) -> List[Dict[str, Any]]:
    """
    Get aggregated expenses data.
    
    This is an alias for get_aggregated_expenses_by_month for compatibility.
    """
    return get_aggregated_expenses_by_month(category, start_date, end_date)
