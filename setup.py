"""
Scheduler package setup
"""
from setuptools import setup, find_packages

setup(
    name='RCTTowerScheduler',
    version='0.0.0.1',
    author='UCSD Engineers for Exploration',
    author_email='e4e@eng.ucsd.edu',
    entry_points={
        'console_scripts': [
            'convertToActive = TowerScheduler.convertToActive:main',
            'scheduler = TowerScheduler.scheduler:main',
            'sleepTimerTester = TowerScheduler.sleepTimerTester:main'
        ]
    },
    packages=find_packages(),
    install_requires=[
        'configparser',
        'datetime',
        'enum',
        'json',
        'multiprocessing',
        'os',
        'pathlib',
        'signal',
        'typing'
    ],
    extras_require={
        'convertToActive': [
            'argparse',
            'schema'
        ],
        'dev': [
            'pytest',
            'coverage',
            'pylint',
            'wheel',
        ]
    },
)
