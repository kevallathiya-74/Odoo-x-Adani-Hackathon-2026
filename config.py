"""
Configuration file for the Maintenance Management System
"""
import os

class Config:
    """Application configuration"""
    
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://keval:UkqdDpDf1QJsyMoh@cluster0.aivlzx3.mongodb.net/?appName=Cluster0')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'maintenance_management')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'adani-hackathon-2026-secret-key')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Application Configuration
    ITEMS_PER_PAGE = 80
    MAX_SEARCH_RESULTS = 1000
    
    # Maintenance Configuration
    MAINTENANCE_TYPES = ['corrective', 'preventive']
    MAINTENANCE_STATES = ['new', 'in_progress', 'done', 'cancelled']
    EQUIPMENT_STATES = ['active', 'under_maintenance', 'scrapped']
    
    # Date Format
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
