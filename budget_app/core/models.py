"""SQLAlchemy models for the budget application."""
from datetime import date, datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Date,
    Float,
    event,
    func,
    text,
    Index,
    DDL,
    event,
    Table,
    MetaData,
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, Session
from sqlalchemy.engine import Engine
from typing import Optional, List, Dict, Any, Generator
import hashlib
import os
import uuid
from contextlib import contextmanager

# Set up SQLAlchemy with SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///budget.db")

# Enable WAL mode and other pragmas for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Set to False to reduce logging and improve performance
)

# Session factory with scoped session for thread safety
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Base class for all models
Base = declarative_base()

def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Transaction(Base):
    """Transaction model for storing expense records."""
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    source = Column(String, default="csv")
    dedupe_key = Column(String(64), unique=True, nullable=False, index=True)

    # Define indexes
    __table_args__ = (
        # Index for monthly aggregation
        Index('idx_txn_month', 
              func.strftime('%Y-%m', transaction_date)),
        
        # Index for case-insensitive description search
        Index('idx_txn_desc_lower', 
              func.lower(description)),
        
        # Composite index for common query patterns
        Index('idx_txn_date_category', 
              transaction_date, 
              category),
    )

    @classmethod
    def generate_dedupe_key(
        cls, 
        transaction_date: date,
        amount: float,
        description: str,
        category: str
    ) -> str:
        """
        Generate a deduplication key for a transaction.
        
        The key is a SHA-256 hash of the following fields:
        - Date in YYYY-MM-DD format
        - Amount formatted to 2 decimal places
        - Description (lowercase, whitespace normalized)
        - Category (lowercase)
        
        This ensures that transactions with the same core attributes
        will generate the same key, allowing for reliable deduplication.
        """
        normalized_desc = " ".join(description.lower().split())
        date_str = transaction_date.strftime("%Y-%m-%d")
        amount_str = f"{float(amount):.2f}"  # Ensure proper float formatting
        
        key_str = f"{date_str}|{amount_str}|{normalized_desc}|{category.lower()}"
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str], default_category: str = "misc") -> 'Transaction':
        """Create a Transaction from a CSV row dictionary."""
        try:
            # Detect CSV format and extract data accordingly
            if 'Debit' in row and 'Credit' in row:
                # Capital One format: Transaction Date, Description, Debit, Credit
                transaction_date_str = row.get("Transaction Date", "").strip()
                description = row.get("Description", "").strip()
                
                # Handle debit/credit amounts - normalize to positive expenses, negative income
                debit = row.get("Debit", "").strip()
                credit = row.get("Credit", "").strip()
                
                if debit and debit != "0":
                    # Debits are expenses - make them positive
                    amount = float(debit)
                elif credit and credit != "0":
                    # Credits are income/refunds - make them negative (since they reduce spending)
                    amount = -float(credit)
                else:
                    amount = 0.0
                    
                category = row.get("Category", default_category).strip().lower()
                
            elif 'Date' in row and 'Transaction Date' not in row:
                # USAA format: Date, Description, Amount
                transaction_date_str = row.get("Date", "").strip()
                description = row.get("Description", "").strip()
                # USAA amounts: make expenses positive (invert the negative amounts)
                amount = abs(float(row.get("Amount", "0").strip()))
                category = row.get("Category", default_category).strip().lower()
                
            elif 'Post Date' in row and 'Type' in row:
                # Chase United format: Transaction Date, Post Date, Description, Category, Type, Amount, Memo
                transaction_date_str = row.get("Transaction Date", "").strip()
                description = row.get("Description", "").strip()
                transaction_type = row.get("Type", "").strip()
                raw_amount = float(row.get("Amount", "0").strip())
                
                # Chase CSV: Sales are negative (expenses), Returns are positive (refunds)
                # We want: Expenses positive, Refunds negative
                if transaction_type.lower() == 'return':
                    # Returns should be negative (money back)
                    amount = -abs(raw_amount)
                else:
                    # Sales/other transactions should be positive (money spent)
                    amount = abs(raw_amount)
                
                # Use the provided category from Chase, but normalize it
                chase_category = row.get("Category", "").strip()
                if chase_category:
                    # Map Chase categories to our standard categories
                    category = cls._normalize_chase_category(chase_category)
                else:
                    category = default_category
                    
            else:
                # Standard format: Transaction Date, Description, Amount, Category
                transaction_date_str = row.get("Transaction Date", "").strip()
                amount = float(row.get("Amount", "0").strip())
                description = row.get("Description", "").strip()
                category = row.get("Category", default_category).strip().lower()
            
            # Parse the date (handle different formats)
            try:
                # Try YYYY-MM-DD format first
                transaction_date = datetime.strptime(transaction_date_str, "%Y-%m-%d").date()
            except ValueError:
                try:
                    # Try MM/DD/YYYY format (Chase uses this)
                    transaction_date = datetime.strptime(transaction_date_str, "%m/%d/%Y").date()
                except ValueError:
                    raise ValueError(f"Unrecognized date format: {transaction_date_str}")
            
            # Generate dedupe key
            dedupe_key = cls.generate_dedupe_key(
                transaction_date=transaction_date,
                amount=amount,
                description=description,
                category=category
            )
            
            return cls(
                transaction_date=transaction_date,
                amount=amount,
                description=description,
                category=category,
                source="csv",
                dedupe_key=dedupe_key
            )
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid CSV row data: {e}")
    
    @classmethod
    def _normalize_chase_category(cls, chase_category: str) -> str:
        """Normalize Chase United categories to our standard categories."""
        from .category_config import get_category_config
        
        config = get_category_config()
        return config.map_external_category(chase_category, 'chase_united')
    
    def __repr__(self) -> str:
        return (
            f"<Transaction(id='{self.id}', "
            f"date='{self.transaction_date}', "
            f"amount={self.amount}, "
            f"category='{self.category}', "
            f"description='{self.description[:20]}...')"
        )

# Create all tables (Alembic will handle this in production)
# This is kept for development convenience only
if os.getenv("CREATE_TABLES", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

# Add a SQLite function for case-insensitive LIKE
def sqlite_ilike(a, b):
    return a.ilike(b)

# Register the function with SQLite
@event.listens_for(Engine, 'begin')
def register_ilike(connection):
    # For SQLite, we need to access the underlying DBAPI connection
    if hasattr(connection.connection, 'create_function'):
        connection.connection.create_function('ilike', 2, sqlite_ilike)
