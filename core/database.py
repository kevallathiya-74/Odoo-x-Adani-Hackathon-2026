"""
MongoDB Database Connection Manager
"""
from pymongo import MongoClient
from pymongo.database import Database
from config import Config

_client = None
_db = None

def init_db():
    """Initialize MongoDB connection"""
    global _client, _db
    
    if _client is None:
        _client = MongoClient(Config.MONGO_URI)
        _db = _client[Config.MONGO_DB_NAME]
        
        # Create indexes for optimization
        _create_indexes()
        
    return _db

def get_db() -> Database:
    """Get database instance"""
    if _db is None:
        return init_db()
    return _db

def _create_indexes():
    """Create database indexes for performance"""
    db = get_db()
    
    # Equipment indexes
    db.equipment.create_index('name')
    db.equipment.create_index('department_id')
    db.equipment.create_index('responsible_id')
    db.equipment.create_index('maintenance_team_id')
    db.equipment.create_index('state')
    db.equipment.create_index([('name', 1), ('state', 1)])
    
    # Maintenance Team indexes
    db.maintenance_team.create_index('name')
    db.maintenance_team.create_index('member_ids')
    
    # Maintenance Request indexes
    db.maintenance_request.create_index('equipment_id')
    db.maintenance_request.create_index('team_id')
    db.maintenance_request.create_index('technician_id')
    db.maintenance_request.create_index('state')
    db.maintenance_request.create_index('maintenance_type')
    db.maintenance_request.create_index('schedule_date')
    db.maintenance_request.create_index([('state', 1), ('schedule_date', 1)])
    db.maintenance_request.create_index([('equipment_id', 1), ('state', 1)])
    
    print("✓ Database indexes created successfully")

def close_db():
    """Close database connection"""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
