from setuptools import setup, find_packages

setup(
    name='budget_app',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'SQLAlchemy>=2.0.0',
        'alembic>=1.12.0',
        'matplotlib>=3.7.0',
        'prettytable>=3.6.0',
        'python-dateutil>=2.8.2',
    ],
    entry_points={
        'console_scripts': [
            'budget-app=budget_app.__main__:main',
        ],
    },
)
