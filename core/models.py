"""
Odoo-style ORM Model base class with MongoDB backend
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId
from .database import get_db
from .fields import Field, fields

class ModelMeta(type):
    """Metaclass for Model to register fields"""
    def __new__(mcs, name, bases, attrs):
        # Extract field definitions
        fields_dict = {}
        for key, value in list(attrs.items()):
            if isinstance(value, Field):
                value.name = key
                fields_dict[key] = value
        
        attrs['_fields'] = fields_dict
        return super().__new__(mcs, name, bases, attrs)

class Model(metaclass=ModelMeta):
    """
    Base Model class with Odoo-style ORM methods
    Implements: create, search, read, write, unlink, browse
    """
    _name = None  # Model name (collection name)
    _description = None  # Human-readable description
    _fields = {}  # Field definitions
    
    def __init__(self, data=None):
        """Initialize model instance"""
        self._data = data or {}
        self._id = self._data.get('_id')
        
    @classmethod
    def _get_collection(cls):
        """Get MongoDB collection for this model"""
        db = get_db()
        return db[cls._name]
    
    @classmethod
    def _prepare_values(cls, vals: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare values for MongoDB storage"""
        prepared = {}
        
        for field_name, value in vals.items():
            if field_name in cls._fields:
                field = cls._fields[field_name]
                prepared[field_name] = field.to_mongo(value)
            else:
                prepared[field_name] = value
        
        # Add metadata
        if '_id' not in prepared:
            prepared['create_date'] = datetime.now()
            prepared['write_date'] = datetime.now()
        else:
            prepared['write_date'] = datetime.now()
            
        return prepared
    
    @classmethod
    def _format_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Format MongoDB record for output"""
        if not record:
            return {}
            
        formatted = {'id': str(record['_id'])}
        
        for field_name, field in cls._fields.items():
            if field_name in record:
                formatted[field_name] = field.from_mongo(record[field_name])
            elif field.default is not None:
                if callable(field.default):
                    formatted[field_name] = field.default()
                else:
                    formatted[field_name] = field.default
                    
        # Include metadata
        if 'create_date' in record:
            formatted['create_date'] = record['create_date'].strftime('%Y-%m-%d %H:%M:%S')
        if 'write_date' in record:
            formatted['write_date'] = record['write_date'].strftime('%Y-%m-%d %H:%M:%S')
            
        return formatted
    
    @classmethod
    def create(cls, vals: Dict[str, Any]) -> 'Model':
        """
        Create new record
        Args:
            vals: Dictionary of field values
        Returns:
            Created record instance
        """
        collection = cls._get_collection()
        prepared_vals = cls._prepare_values(vals)
        
        # Validate required fields
        for field_name, field in cls._fields.items():
            if field.required and field_name not in prepared_vals:
                if field.default is not None:
                    if callable(field.default):
                        prepared_vals[field_name] = field.default()
                    else:
                        prepared_vals[field_name] = field.default
                else:
                    raise ValueError(f"Required field '{field_name}' is missing")
        
        result = collection.insert_one(prepared_vals)
        prepared_vals['_id'] = result.inserted_id
        
        return cls(prepared_vals)
    
    @classmethod
    def search(cls, domain: List = None, limit: int = None, 
               offset: int = 0, order: str = None) -> List['Model']:
        """
        Search records
        Args:
            domain: Search criteria in Odoo format [('field', 'operator', 'value')]
            limit: Maximum number of records
            offset: Number of records to skip
            order: Sort order (e.g., 'name ASC', 'create_date DESC')
        Returns:
            List of model instances
        """
        collection = cls._get_collection()
        
        # Convert Odoo domain to MongoDB query
        query = cls._domain_to_mongo(domain or [])
        
        # Build cursor
        cursor = collection.find(query).skip(offset)
        
        if limit:
            cursor = cursor.limit(limit)
            
        if order:
            sort_list = cls._parse_order(order)
            cursor = cursor.sort(sort_list)
        
        return [cls(record) for record in cursor]
    
    @classmethod
    def search_count(cls, domain: List = None) -> int:
        """Count records matching domain"""
        collection = cls._get_collection()
        query = cls._domain_to_mongo(domain or [])
        return collection.count_documents(query)
    
    @classmethod
    def browse(cls, ids) -> List['Model']:
        """
        Browse records by ID(s)
        Args:
            ids: Single ID or list of IDs
        Returns:
            List of model instances
        """
        if not ids:
            return []
            
        if not isinstance(ids, list):
            ids = [ids]
        
        collection = cls._get_collection()
        object_ids = [ObjectId(id_) if isinstance(id_, str) else id_ for id_ in ids]
        
        records = collection.find({'_id': {'$in': object_ids}})
        return [cls(record) for record in records]
    
    def write(self, vals: Dict[str, Any]) -> bool:
        """
        Update record
        Args:
            vals: Dictionary of field values to update
        Returns:
            True if successful
        """
        if not self._id:
            raise ValueError("Cannot update record without ID")
        
        collection = self._get_collection()
        prepared_vals = self._prepare_values(vals)
        
        result = collection.update_one(
            {'_id': self._id},
            {'$set': prepared_vals}
        )
        
        # Update internal data
        self._data.update(prepared_vals)
        
        return result.modified_count > 0
    
    def unlink(self) -> bool:
        """
        Delete record
        Returns:
            True if successful
        """
        if not self._id:
            raise ValueError("Cannot delete record without ID")
        
        collection = self._get_collection()
        result = collection.delete_one({'_id': self._id})
        
        return result.deleted_count > 0
    
    @classmethod
    def _domain_to_mongo(cls, domain: List) -> Dict:
        """Convert Odoo domain to MongoDB query"""
        if not domain:
            return {}
        
        query = {}
        for condition in domain:
            if len(condition) != 3:
                continue
                
            field, operator, value = condition
            
            if operator == '=':
                query[field] = value
            elif operator == '!=':
                query[field] = {'$ne': value}
            elif operator == 'in':
                query[field] = {'$in': value}
            elif operator == 'not in':
                query[field] = {'$nin': value}
            elif operator == '>':
                query[field] = {'$gt': value}
            elif operator == '>=':
                query[field] = {'$gte': value}
            elif operator == '<':
                query[field] = {'$lt': value}
            elif operator == '<=':
                query[field] = {'$lte': value}
            elif operator == 'like':
                query[field] = {'$regex': value, '$options': 'i'}
            elif operator == 'ilike':
                query[field] = {'$regex': value, '$options': 'i'}
                
        return query
    
    @classmethod
    def _parse_order(cls, order: str) -> List:
        """Parse Odoo order string to MongoDB sort list"""
        sort_list = []
        for part in order.split(','):
            part = part.strip()
            if ' ' in part:
                field, direction = part.split()
                sort_direction = -1 if direction.upper() == 'DESC' else 1
            else:
                field = part
                sort_direction = 1
            sort_list.append((field, sort_direction))
        return sort_list
    
    def read(self, fields: List[str] = None) -> Dict[str, Any]:
        """
        Read record fields
        Args:
            fields: List of field names to read (None = all fields)
        Returns:
            Dictionary of field values
        """
        formatted = self._format_record(self._data)
        
        if fields:
            return {k: v for k, v in formatted.items() if k in fields or k == 'id'}
        
        return formatted
    
    def __getattribute__(self, name):
        """Allow accessing fields as attributes"""
        # First check if it's a private attribute or method
        if name.startswith('_') or name in ['read', 'write', 'unlink', 'browse', 'create', 'search', 'search_count']:
            return super().__getattribute__(name)
        
        # Get _data and _fields through super to avoid recursion
        try:
            _data = super().__getattribute__('_data')
            _fields = super().__getattribute__('_fields')
        except AttributeError:
            return super().__getattribute__(name)
        
        # If it's a field name, return the value from _data
        if name in _fields:
            if name in _data:
                field = _fields[name]
                return field.from_mongo(_data[name])
            else:
                # Return default if not in data
                field = _fields[name]
                if field.default is not None:
                    if callable(field.default):
                        return field.default()
                    return field.default
                return None
        
        # Otherwise use normal attribute access
        return super().__getattribute__(name)
    
    def __setattr__(self, name, value):
        """Allow setting fields as attributes"""
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in self._fields:
            self._data[name] = self._fields[name].to_mongo(value)
        else:
            super().__setattr__(name, value)
