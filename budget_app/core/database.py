"""
Database session management and core operations for the budget application.

This module provides:
- Session management with context managers
- Core database operations (CRUD)
- Bulk import functionality with deduplication
- Query helpers for common operations
"""
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
import logging

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import SessionLocal, Transaction, Category, CategoryKeyword, Base, engine

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
        
        # Time of day analysis (simplified - using hash of transaction data as proxy)
        # In a real app, you'd have actual timestamps
        time_patterns = [0] * 24  # Initialize array for 24 hours
        
        # Get all transactions for time analysis
        all_transactions = base_query.all()
        for txn in all_transactions:
            # Use a hash of the transaction data to simulate time distribution
            # This creates a pseudo-random but consistent distribution
            hash_value = hash(f"{txn.id}{txn.description}{txn.amount}")
            hour = abs(hash_value) % 24
            time_patterns[hour] += float(txn.amount) if txn.amount > 0 else 0
        
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


# Category Management Functions

def get_all_categories() -> List[Dict[str, Any]]:
    """
    Get all categories with their keywords.
    
    Returns:
        List of category dictionaries with keywords
    """
    with get_db() as db:
        categories = db.query(Category).filter(Category.is_active == "true").all()
        
        result = []
        for category in categories:
            keywords = [kw.keyword for kw in category.keywords if kw.is_active == "true"]
            result.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'color': category.color,
                'keywords': keywords,
                'keyword_count': len(keywords),
                'created_at': category.created_at.isoformat() if category.created_at else None
            })
        
        return result


def create_category(name: str, description: str = "", color: str = "#6c757d", keywords: List[str] = None) -> Dict[str, Any]:
    """
    Create a new category with optional keywords.
    
    Args:
        name: Category name
        description: Category description
        color: Hex color code
        keywords: List of keywords for this category
        
    Returns:
        Dict with category information
    """
    with get_db() as db:
        # Check if category already exists
        existing = db.query(Category).filter(func.lower(Category.name) == name.lower()).first()
        if existing:
            raise ValueError(f"Category '{name}' already exists")
        
        # Create category
        category = Category(
            name=name.strip(),
            description=description.strip(),
            color=color,
            is_active="true"
        )
        db.add(category)
        db.flush()  # Get the ID
        
        # Add keywords
        if keywords:
            for keyword in keywords:
                if keyword.strip():
                    kw = CategoryKeyword(
                        category_id=category.id,
                        keyword=keyword.strip().lower(),
                        is_active="true"
                    )
                    db.add(kw)
        
        db.commit()
        
        return {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'color': category.color,
            'keywords': keywords or []
        }


def update_category(category_id: str, name: str = None, description: str = None, 
                   color: str = None, keywords: List[str] = None) -> Dict[str, Any]:
    """
    Update an existing category.
    
    Args:
        category_id: Category ID to update
        name: New name (optional)
        description: New description (optional)
        color: New color (optional)
        keywords: New keywords list (optional, replaces existing)
        
    Returns:
        Dict with updated category information
    """
    with get_db() as db:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise ValueError(f"Category with ID '{category_id}' not found")
        
        # Update category fields
        if name is not None:
            # Check for duplicate name
            existing = db.query(Category).filter(
                func.lower(Category.name) == name.lower(),
                Category.id != category_id
            ).first()
            if existing:
                raise ValueError(f"Category '{name}' already exists")
            category.name = name.strip()
        
        if description is not None:
            category.description = description.strip()
        
        if color is not None:
            category.color = color
        
        # Update keywords if provided
        if keywords is not None:
            # Remove existing keywords
            db.query(CategoryKeyword).filter(CategoryKeyword.category_id == category_id).delete()
            
            # Add new keywords
            for keyword in keywords:
                if keyword.strip():
                    kw = CategoryKeyword(
                        category_id=category_id,
                        keyword=keyword.strip().lower(),
                        is_active="true"
                    )
                    db.add(kw)
        
        db.commit()
        
        # Return updated category
        updated_keywords = [kw.keyword for kw in category.keywords if kw.is_active == "true"]
        return {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'color': category.color,
            'keywords': updated_keywords
        }


def delete_category(category_id: str) -> bool:
    """
    Delete a category (soft delete by setting is_active to false).
    
    Args:
        category_id: Category ID to delete
        
    Returns:
        bool: True if deleted successfully
    """
    with get_db() as db:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return False
        
        # Soft delete category and its keywords
        category.is_active = "false"
        db.query(CategoryKeyword).filter(CategoryKeyword.category_id == category_id).update(
            {"is_active": "false"}
        )
        
        db.commit()
        return True


def get_category_keywords_map() -> Dict[str, str]:
    """
    Get a mapping of keywords to category names for categorization.
    
    Returns:
        Dict mapping keywords to category names
    """
    with get_db() as db:
        keywords = db.query(CategoryKeyword, Category).join(
            Category, CategoryKeyword.category_id == Category.id
        ).filter(
            CategoryKeyword.is_active == "true",
            Category.is_active == "true"
        ).order_by(CategoryKeyword.priority.desc()).all()
        
        keyword_map = {}
        for keyword_obj, category in keywords:
            keyword_map[keyword_obj.keyword.lower()] = category.name
        
        return keyword_map


def get_weekly_spending_data(
    start_date: Optional[Union[date, str]] = None,
    end_date: Optional[Union[date, str]] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get weekly spending data for the specified date range.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        category: Optional category filter
        
    Returns:
        List of weekly spending data
    """
    with get_db() as db:
        # Base query
        base_query = db.query(Transaction)
        
        # Apply filters
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            base_query = base_query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            base_query = base_query.filter(Transaction.transaction_date <= end_date)
        if category and category != 'all':
            base_query = base_query.filter(Transaction.category == category)
        
        # Only positive amounts (expenses)
        base_query = base_query.filter(Transaction.amount > 0)
        
        # Group by week using SQLite's date functions
        weekly_query = base_query.with_entities(
            func.strftime('%Y-W%W', Transaction.transaction_date).label('week'),
            func.sum(Transaction.amount).label('total'),
            func.min(Transaction.transaction_date).label('week_start')
        ).group_by(func.strftime('%Y-W%W', Transaction.transaction_date)).order_by('week_start')
        
        results = weekly_query.all()
        
        weekly_data = []
        for result in results:
            # Format week label
            week_start = result.week_start
            week_end = week_start + timedelta(days=6)
            week_label = f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"
            
            weekly_data.append({
                'week': result.week,
                'week_label': week_label,
                'total': float(result.total) if result.total else 0.0,
                'week_start': result.week_start.isoformat() if result.week_start else None
            })
        
        return weekly_data


def get_category_budget_comparison(
    start_date: Optional[Union[date, str]] = None,
    end_date: Optional[Union[date, str]] = None
) -> List[Dict[str, Any]]:
    """
    Get category spending vs budget comparison.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of category budget comparison data
    """
    with get_db() as db:
        # Get all active categories with budgets
        categories = db.query(Category).filter(Category.is_active == "true").all()
        
        # Calculate date range for budget calculation
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Calculate number of months in the period for budget scaling
        if start_date and end_date:
            months_in_period = ((end_date.year - start_date.year) * 12 + 
                              (end_date.month - start_date.month) + 1)
        else:
            months_in_period = 1
        
        comparison_data = []
        
        for category in categories:
            # Get spending for this category in the date range
            spending_query = db.query(func.sum(Transaction.amount)).filter(
                Transaction.category == category.name.lower(),
                Transaction.amount > 0  # Only expenses
            )
            
            if start_date:
                spending_query = spending_query.filter(Transaction.transaction_date >= start_date)
            if end_date:
                spending_query = spending_query.filter(Transaction.transaction_date <= end_date)
            
            total_spent = spending_query.scalar() or 0.0
            
            # Calculate budget for the period
            monthly_budget = category.monthly_budget or 0.0
            period_budget = monthly_budget * months_in_period
            
            # Calculate percentage and status
            if period_budget > 0:
                percentage = (total_spent / period_budget) * 100
                if percentage <= 80:
                    status = "under"
                elif percentage <= 100:
                    status = "near"
                else:
                    status = "over"
            else:
                percentage = 0
                status = "no_budget"
            
            comparison_data.append({
                'category_id': category.id,
                'category_name': category.name,
                'color': category.color,
                'total_spent': float(total_spent),
                'monthly_budget': float(monthly_budget),
                'period_budget': float(period_budget),
                'percentage': float(percentage),
                'remaining': float(period_budget - total_spent),
                'status': status,
                'months_in_period': months_in_period
            })
        
        # Sort by spending amount (highest first)
        comparison_data.sort(key=lambda x: x['total_spent'], reverse=True)
        
        return comparison_data


def update_category_budget(category_id: str, monthly_budget: float) -> bool:
    """
    Update the monthly budget for a category.
    
    Args:
        category_id: Category ID to update
        monthly_budget: New monthly budget amount
        
    Returns:
        bool: True if updated successfully
    """
    with get_db() as db:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return False
        
        category.monthly_budget = monthly_budget
        db.commit()
        return True


def get_monthly_trends_data(
    start_date: Optional[Union[date, str]] = None,
    end_date: Optional[Union[date, str]] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get monthly trends data showing expenses and income over time.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        category: Optional category filter
        
    Returns:
        Dict with monthly trends data
    """
    with get_db() as db:
        # Base query
        base_query = db.query(Transaction)
        
        # Apply filters
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            base_query = base_query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            base_query = base_query.filter(Transaction.transaction_date <= end_date)
        if category and category != 'all':
            base_query = base_query.filter(Transaction.category == category)
        
        # Group by month and separate expenses/income
        monthly_query = base_query.with_entities(
            func.strftime('%Y-%m', Transaction.transaction_date).label('month'),
            func.sum(func.case([(Transaction.amount > 0, Transaction.amount)], else_=0)).label('expenses'),
            func.sum(func.case([(Transaction.amount < 0, func.abs(Transaction.amount))], else_=0)).label('income')
        ).group_by(func.strftime('%Y-%m', Transaction.transaction_date)).order_by('month')
        
        results = monthly_query.all()
        
        months = []
        expenses = []
        income = []
        
        for result in results:
            # Format month label
            month_date = datetime.strptime(result.month + '-01', '%Y-%m-%d')
            month_label = month_date.strftime('%b %Y')
            
            months.append(month_label)
            expenses.append(float(result.expenses) if result.expenses else 0.0)
            income.append(float(result.income) if result.income else 0.0)
        
        return {
            'months': months,
            'expenses': expenses,
            'income': income
        }


def recategorize_existing_transactions() -> Dict[str, int]:
    """
    Re-categorize all existing transactions using current categorization rules.
    
    Returns:
        Dict with counts of updated transactions
    """
    # First, get the keyword map outside of any transaction context
    keyword_map = get_category_keywords_map()
    
    with get_db() as db:
        # Get all transaction data as simple tuples to avoid session issues
        transaction_data = db.query(
            Transaction.id,
            Transaction.description,
            Transaction.category
        ).all()
        
        updated_count = 0
        unchanged_count = 0
        total_count = len(transaction_data)
        
        # Process each transaction
        for trans_id, description, current_category in transaction_data:
            # Skip transactions that start with '+' (manually categorized)
            if description and description.startswith('+'):
                unchanged_count += 1
                continue
            
            # Clean up values
            description = description or ""
            current_category = current_category or ""
            
            # Get new category using keyword map (avoid database calls)
            new_category = _categorize_with_keyword_map(description, keyword_map)
            
            # Update if category changed
            if new_category != current_category.lower():
                # Update the transaction in the database directly
                db.query(Transaction).filter(
                    Transaction.id == trans_id
                ).update({
                    'category': new_category
                })
                updated_count += 1
            else:
                unchanged_count += 1
        
        # Commit all changes at once
        db.commit()
        
        return {
            'updated': updated_count,
            'unchanged': unchanged_count,
            'total': total_count
        }


def _categorize_with_keyword_map(description: str, keyword_map: Dict[str, str]) -> str:
    """
    Categorize a transaction using a pre-loaded keyword map.
    
    Args:
        description: Transaction description
        keyword_map: Dictionary mapping keywords to category names
        
    Returns:
        Category name (lowercase)
    """
    if not description:
        return "misc"
    
    description_clean = description.lower().strip()
    
    # Check keywords in priority order (already sorted by priority in the map)
    for keyword, category_name in keyword_map.items():
        if keyword in description_clean:
            return category_name.lower()
    
    # Fallback to hardcoded categorization if no database keywords match
    from .categorization import _categorize_with_hardcoded_keywords
    return _categorize_with_hardcoded_keywords(description_clean)


def import_budgets_from_csv(file_path: str) -> Dict[str, int]:
    """
    Import budget amounts from a CSV file.
    
    Args:
        file_path: Path to the CSV file with Category,Amount columns
        
    Returns:
        Dict with import results
    """
    import csv
    
    updated_count = 0
    created_count = 0
    error_count = 0
    errors = []
    
    with get_db() as db:
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        category_name = row.get('Category', '').strip()
                        amount_str = row.get('Amount', '').strip()
                        
                        if not category_name or not amount_str:
                            continue
                        
                        # Parse amount
                        amount = float(amount_str.replace(',', ''))
                        
                        # Skip negative amounts or zero (except for categories that might legitimately be 0)
                        if amount < 0:
                            continue
                        
                        # Find existing category (case-insensitive)
                        category = db.query(Category).filter(
                            func.lower(Category.name) == category_name.lower()
                        ).first()
                        
                        if category:
                            # Update existing category budget
                            category.monthly_budget = amount
                            updated_count += 1
                        else:
                            # Create new category with budget
                            category = Category(
                                name=category_name,
                                description=f"Imported from budget CSV",
                                monthly_budget=amount,
                                is_active="true"
                            )
                            db.add(category)
                            created_count += 1
                            
                    except (ValueError, KeyError) as e:
                        error_count += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                        continue
            
            db.commit()
            
        except FileNotFoundError:
            raise ValueError(f"Budget file not found: {file_path}")
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error reading budget file: {str(e)}")
    
    return {
        'updated': updated_count,
        'created': created_count,
        'errors': error_count,
        'error_details': errors,
        'total_processed': updated_count + created_count + error_count
    }
