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
            'scheduler = TowerScheduler.scheduler:main',
            'sleepTimerTester = TowerScheduler.sleepTimerTester:main'
        ]
    },
    packages=find_packages(),
    install_requires=[],
    extras_require={
        'dev': [
            'pytest',
            'coverage',
            'pylint',
            'wheel',
        ]
    },
)
