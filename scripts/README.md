# Scripts Quick Start Guide

This folder contains powerful analysis and management scripts for your budget application. Each script is designed for specific tasks and can be run independently.

## 📊 Analysis Scripts

### `1.5-expense_trends.py`
**Analyzes misc transactions and suggests recategorization based on description patterns.**

```bash
# Analyze misc transactions for potential recategorization
python scripts/1.5-expense_trends.py
```

**What it does:**
- Finds all transactions in 'misc' category
- Shows most common descriptions
- Suggests new categories based on keyword patterns
- Displays before/after category counts

**Example Output:**
```
Most common descriptions in the 'Misc' category:
AT&T: 5
Verizon: 4
PARTY CITY 1090: 3

Proposed new categories for 'Misc' transactions:
Misc: 119
Shopping: 3
```

---

### `4-deep_keyword_analysis.py`
**Analyzes all transactions containing a specific keyword and exports results.**

```bash
# Find all transactions containing "TARGET"
python scripts/4-deep_keyword_analysis.py TARGET

# Save to custom directory
python scripts/4-deep_keyword_analysis.py "CHICK-FIL-A" --output-dir custom_output/

# Find Walmart transactions
python scripts/4-deep_keyword_analysis.py "WAL-MART"
```

**What it does:**
- Searches database for transactions containing keyword
- Shows summary statistics (count, total amount, average)
- Exports results to CSV file
- Displays sample transactions

**Example Output:**
```
Found 43 transactions containing 'Target'
Total amount: $2007.86
Average amount: $46.69
Filtered data saved to data/outputs/Output/Target_history.csv
```

---

## 🏷️ Category Management Scripts

### `category_manager.py`
**Comprehensive category analysis and bulk update tool.**

```bash
# Review all categories with sample transactions
python scripts/category_manager.py review

# Analyze misc category for recategorization opportunities
python scripts/category_manager.py analyze --category misc

# Show suggested updates for misc transactions
python scripts/category_manager.py suggest --category misc

# Bulk update AT&T transactions from misc to utilities
python scripts/category_manager.py update --category misc --new-category utilities --pattern "AT&T"

# Interactive mode for real-time management
python scripts/category_manager.py interactive
```

**What it does:**
- Reviews categories with sample transactions
- Identifies miscategorized transactions using keyword patterns
- Provides bulk update capabilities with confirmation
- Shows suggested improvements for problem categories

---

### `update_categories.py`
**Quick manual updates for individual transactions or patterns.**

```bash
# Update single transaction by ID (supports partial IDs)
python scripts/update_categories.py single --id 63ced0fc --category utilities

# Update all transactions containing "VERIZON" to utilities
python scripts/update_categories.py batch --pattern "VERIZON" --category utilities

# Update only transactions in 'misc' category containing "TARGET"
python scripts/update_categories.py batch --pattern "TARGET" --category shopping --old-category misc
```

**What it does:**
- Updates individual transactions by ID
- Batch updates by description pattern
- Confirms changes before applying
- Shows updated transaction details

---

## ⚙️ Configuration Management Scripts

### `manage_categories_config.py`
**Manages the YAML configuration file for category keywords and mappings.**

```bash
# View all categories and keywords
python scripts/manage_categories_config.py list

# View external category mappings (Chase, Capital One, USAA)
python scripts/manage_categories_config.py mappings

# Add new keyword to a category
python scripts/manage_categories_config.py add --category utilities --keyword "spectrum"

# Remove keyword from category
python scripts/manage_categories_config.py remove --category misc --keyword "old_keyword"

# Test categorization on a description
python scripts/manage_categories_config.py test --description "NETFLIX MONTHLY SUBSCRIPTION"

# Search for existing keywords
python scripts/manage_categories_config.py search --search-term "verizon"

# Interactive management mode
python scripts/manage_categories_config.py interactive
```

**What it does:**
- Manages `config/categories.yaml` file
- Adds/removes keywords without code changes
- Tests categorization rules
- Searches existing keyword patterns

---

## 🔄 Recategorization Scripts

### `recategorize_all_transactions.py`
**Comprehensive recategorization using new YAML configuration rules.**

```bash
# Analyze all transactions for potential improvements
python scripts/recategorize_all_transactions.py analyze

# Show detailed changes for specific categories
python scripts/recategorize_all_transactions.py show --filter misc --limit 20

# Test changes without applying (dry run)
python scripts/recategorize_all_transactions.py apply --dry-run

# Apply all changes with confirmation
python scripts/recategorize_all_transactions.py apply

# Apply only shopping-related changes
python scripts/recategorize_all_transactions.py apply --filter shopping

# Export detailed report to CSV
python scripts/recategorize_all_transactions.py export

# Interactive mode (no command-line args)
python scripts/recategorize_all_transactions.py
```

**What it does:**
- Analyzes all 800+ transactions against new configuration
- Identifies categorization improvements
- Provides detailed before/after reports
- Supports selective application by category
- Exports comprehensive change reports

**Example Output:**
```
📊 Total Transactions: 842
✅ No Change Needed: 465 (55.2%)
🔄 Changes Proposed: 377 (44.8%)

TOP CHANGE PATTERNS:
   31 × merchandise → target
   22 × dining → misc
   15 × misc → transfer
```

---

### `apply_safe_recategorizations.py`
**Applies only the safest, most obvious categorization improvements.**

```bash
# Apply safe improvements with interactive confirmation
python scripts/apply_safe_recategorizations.py
```

**What it does:**
- Focuses on obvious improvements (misc → proper categories)
- Asks for confirmation for each change type
- Shows examples before applying
- Safer alternative to full recategorization

---

## 🛠️ Advanced User Scripts

### `quick_category_commands.py`
**Python functions for power users and custom scripting.**

```bash
# Run in Python REPL for advanced operations
python scripts/quick_category_commands.py
```

**Available Functions:**
```python
quick_overview()                           # Category counts
find_transactions('pattern', limit=10)     # Search transactions
update_category('partial_id', 'new_cat')   # Update by ID
bulk_update('pattern', 'new_cat')          # Bulk update
show_problem_categories()                   # Show categories needing review
```

---

## 📈 Workflow Recommendations

### 🚀 Quick Start (New Users)
```bash
# 1. See current category overview
python scripts/category_manager.py review

# 2. Analyze for improvements
python scripts/recategorize_all_transactions.py analyze

# 3. Apply safe improvements
python scripts/apply_safe_recategorizations.py
```

### 🔧 Regular Maintenance
```bash
# 1. Find specific issues
python scripts/4-deep_keyword_analysis.py "UNKNOWN_MERCHANT"

# 2. Update configuration
python scripts/manage_categories_config.py add --category utilities --keyword "new_company"

# 3. Apply targeted fixes
python scripts/category_manager.py update --category misc --new-category utilities --pattern "SPECTRUM"
```

### 📊 Deep Analysis
```bash
# 1. Comprehensive analysis
python scripts/recategorize_all_transactions.py analyze

# 2. Export detailed report
python scripts/recategorize_all_transactions.py export

# 3. Review and apply selectively
python scripts/recategorize_all_transactions.py show --filter shopping
python scripts/recategorize_all_transactions.py apply --filter shopping --dry-run
python scripts/recategorize_all_transactions.py apply --filter shopping
```

### 🎯 Interactive Management
```bash
# Configuration management
python scripts/manage_categories_config.py interactive

# Category analysis and updates
python scripts/category_manager.py interactive

# Full recategorization workflow
python scripts/recategorize_all_transactions.py
```

---

## 📁 Output Locations

- **CSV Reports**: `data/outputs/Output/`
- **Analysis Charts**: `data/outputs/Output/`
- **Configuration**: `config/categories.yaml`

## 💡 Tips

1. **Always test first**: Use `--dry-run` flags when available
2. **Start small**: Use filters to apply changes gradually
3. **Check results**: Review outputs before applying large changes
4. **Backup data**: Your database is automatically backed up, but export reports for reference
5. **Interactive mode**: Use interactive modes for complex workflows

## 🆘 Common Tasks

```bash
# Fix AT&T miscategorized as misc
python scripts/update_categories.py batch --pattern "AT&T" --category utilities --old-category misc

# Add new company to groceries
python scripts/manage_categories_config.py add --category groceries --keyword "fresh_market"

# See all Verizon transactions
python scripts/4-deep_keyword_analysis.py "VERIZON"

# Clean up misc category
python scripts/category_manager.py suggest --category misc
```

---

**Need Help?** All scripts support `--help` flag for detailed usage information:
```bash
python scripts/[script_name].py --help
```
