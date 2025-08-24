"""
Flask web application for the budget app.

Provides a modern web interface with intuitive data selections,
real-time updates, and responsive design.
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import os
import json
from datetime import datetime, date
from typing import Dict, List, Any

from ..core.database import (
    get_transactions,
    get_categories,
    get_aggregated_expenses,
    import_transactions_from_csv,
    delete_transaction,
    get_all_categories,
    create_category,
    update_category,
    delete_category,
    get_spending_patterns
)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Initialize SocketIO for real-time updates
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @app.route('/')
    def dashboard():
        """Main dashboard page."""
        return render_template('dashboard.html')
    
    @app.route('/api/categories')
    def api_categories():
        """Get all categories with totals."""
        try:
            categories = get_categories()
            return jsonify({'success': True, 'data': categories})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/transactions')
    def api_transactions():
        """Get filtered transactions."""
        try:
            # Get query parameters
            category = request.args.get('category', 'all')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            keyword = request.args.get('keyword')
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            sort_by = request.args.get('sort_by', 'date')
            order = request.args.get('order', 'desc')
            
            # Convert dates
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Get transactions
            if category == 'all':
                transactions, total = get_transactions(
                    category=None,  # None means all categories
                    keyword=keyword,
                    start_date=start_date,
                    end_date=end_date,
                    sort_by=sort_by,
                    order=order,
                    limit=limit,
                    offset=offset
                )
            else:
                transactions, total = get_transactions(
                    category=category,
                    keyword=keyword,
                    start_date=start_date,
                    end_date=end_date,
                    sort_by=sort_by,
                    order=order,
                    limit=limit,
                    offset=offset
                )
            
            # Convert to JSON-serializable format
            transaction_data = []
            for txn in transactions:
                transaction_data.append({
                    'id': txn.id,
                    'date': txn.transaction_date.isoformat(),
                    'description': txn.description,
                    'amount': float(txn.amount),
                    'category': txn.category,
                    'source': txn.source
                })
            
            return jsonify({
                'success': True,
                'data': transaction_data,
                'total': total,
                'limit': limit
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/expenses/aggregated')
    def api_aggregated_expenses():
        """Get aggregated expenses by month."""
        try:
            category = request.args.get('category', 'all')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Convert dates
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if category == 'all':
                # Get aggregated data for all categories
                categories = get_categories()
                aggregated_data = []
                for cat in categories:
                    cat_data = get_aggregated_expenses(
                        category=cat['category'],
                        start_date=start_date,
                        end_date=end_date
                    )
                    aggregated_data.append({
                        'category': cat['category'],
                        'data': cat_data
                    })
            else:
                aggregated_data = get_aggregated_expenses(
                    category=category,
                    start_date=start_date,
                    end_date=end_date
                )
            
            return jsonify({'success': True, 'data': aggregated_data})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/spending/patterns')
    def api_spending_patterns():
        """Get spending patterns data."""
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            data = get_spending_patterns(start_date, end_date)
            return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/import', methods=['POST'])
    def api_import():
        """Import transactions from CSV."""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            # Save uploaded file temporarily
            upload_dir = os.path.join(app.root_path, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, file.filename)
            file.save(file_path)
            
            # Get import options
            source = request.form.get('source', 'csv')
            auto_categorize = request.form.get('auto_categorize', 'true').lower() == 'true'
            
            # Import transactions with auto-categorization
            result = import_transactions_from_csv(
                file_path, 
                default_category="misc",  # Fallback for unmatched transactions
                source=source,
                auto_categorize=auto_categorize
            )
            
            # Clean up uploaded file
            os.remove(file_path)
            
            # Emit real-time update
            socketio.emit('import_complete', {
                'inserted': result['inserted'],
                'duplicates': result['duplicates'],
                'errors': result['errors']
            })
            
            return jsonify({
                'success': True,
                'message': f"Import complete: {result['inserted']} inserted, {result['duplicates']} duplicates",
                'data': result
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/transactions/<transaction_id>', methods=['DELETE'])
    def api_delete_transaction(transaction_id):
        """Delete a transaction."""
        try:
            success = delete_transaction(transaction_id)
            if success:
                # Emit real-time update
                socketio.emit('transaction_deleted', {'id': transaction_id})
                return jsonify({'success': True, 'message': 'Transaction deleted'})
            else:
                return jsonify({'success': False, 'error': 'Transaction not found'}), 404
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/upload')
    def upload_page():
        """File upload page."""
        return render_template('upload.html')
    
    @app.route('/transactions')
    def transactions_page():
        """Transactions page."""
        return render_template('transactions.html')
    
    @app.route('/analytics')
    def analytics_page():
        """Analytics page."""
        return render_template('analytics.html')
    
    @app.route('/categories')
    def categories_page():
        """Categories management page."""
        return render_template('categories.html')
    
    # Category Management API Endpoints
    
    @app.route('/api/categories/manage')
    def api_manage_categories():
        """Get all categories with keywords for management."""
        try:
            categories = get_all_categories()
            return jsonify({'success': True, 'data': categories})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/categories/manage', methods=['POST'])
    def api_create_category():
        """Create a new category."""
        try:
            data = request.get_json()
            if not data or not data.get('name'):
                return jsonify({'success': False, 'error': 'Category name is required'}), 400
            
            result = create_category(
                name=data['name'],
                description=data.get('description', ''),
                color=data.get('color', '#6c757d'),
                keywords=data.get('keywords', [])
            )
            
            return jsonify({'success': True, 'data': result})
            
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/categories/manage/<category_id>', methods=['PUT'])
    def api_update_category(category_id):
        """Update an existing category."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            result = update_category(
                category_id=category_id,
                name=data.get('name'),
                description=data.get('description'),
                color=data.get('color'),
                keywords=data.get('keywords')
            )
            
            return jsonify({'success': True, 'data': result})
            
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/categories/manage/<category_id>', methods=['DELETE'])
    def api_delete_category(category_id):
        """Delete a category."""
        try:
            success = delete_category(category_id)
            if success:
                return jsonify({'success': True, 'message': 'Category deleted successfully'})
            else:
                return jsonify({'success': False, 'error': 'Category not found'}), 404
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return app
