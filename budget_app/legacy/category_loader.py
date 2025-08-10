import csv

def get_categories(file_path):
    categories = set()
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            category = row[0]
            categories.add(category)
    return list(categories)
