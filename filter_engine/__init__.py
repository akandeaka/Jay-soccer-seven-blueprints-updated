"""
Filter Engine for JAY SOCCER BLUEPRINTS
Version: 1.0.0

This package filters blueprint matches based on deep data insights.
"""

# Import the main classes for easy access
from .blueprint_filter import BlueprintFilterEngine
from .telegram_integration import TelegramIntegrator
from .config import FilterConfig, IntegrationConfig

# Package metadata
__version__ = "1.0.0"
__author__ = "Jay Soccer Blueprints"
__description__ = "Advanced filter engine for blueprint match selection"

# What gets imported with "from filter_engine import *"
__all__ = [
    'BlueprintFilterEngine',
    'TelegramIntegrator', 
    'FilterConfig',
    'IntegrationConfig'
]
