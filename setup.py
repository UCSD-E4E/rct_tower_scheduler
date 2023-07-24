"""
Scheduler package setup
"""
from setuptools import setup, find_packages

setup(
    name='RCTTowerScheduler',
    version='0.0.0.1',
    author='UCSD Engineers for Exploration',
    author_email='e4e@ucsd.edu',
    entry_points={
        'console_scripts': [
            'convertToActive = TowerScheduler.convertToActive:main',
            'scheduler = TowerScheduler.scheduler:main',
            'sleepTimerTester = TowerScheduler.sleepTimerTester:main'
        ]
    },
    packages=find_packages(),
    install_requires=[
        'argparse',
        'configparser',
        'datetime',
        'enum',
        'json',
        'multiprocessing',
        'os',
        'pathlib',
        'schema',
        'signal',
        'typing'
    ],
    extras_require={
        'dev': [
            'pytest',
            'coverage',
            'pylint',
            'wheel',
        ]
    },
)
