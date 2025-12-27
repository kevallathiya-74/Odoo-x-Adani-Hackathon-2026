"""
Core ORM layer for Odoo-style MongoDB integration
"""
from .database import get_db, init_db
from .models import Model, fields

__all__ = ['get_db', 'init_db', 'Model', 'fields']
