"""
Odoo-style field definitions for MongoDB models
"""
from datetime import datetime
from typing import Any, Callable, Optional

class Field:
    """Base field class"""
    def __init__(self, string=None, required=False, readonly=False, 
                 default=None, compute=None, store=True, index=False,
                 help=None):
        self.string = string
        self.required = required
        self.readonly = readonly
        self.default = default
        self.compute = compute
        self.store = store
        self.index = index
        self.help = help
        self.name = None  # Set by metaclass
        
    def to_mongo(self, value):
        """Convert Python value to MongoDB value"""
        return value
        
    def from_mongo(self, value):
        """Convert MongoDB value to Python value"""
        return value

class Char(Field):
    """Character field"""
    def __init__(self, size=None, **kwargs):
        super().__init__(**kwargs)
        self.size = size

class Text(Field):
    """Text field"""
    pass

class Integer(Field):
    """Integer field"""
    def to_mongo(self, value):
        if value is None:
            return None
        return int(value)

class Float(Field):
    """Float field"""
    def to_mongo(self, value):
        if value is None:
            return None
        return float(value)

class Boolean(Field):
    """Boolean field"""
    def to_mongo(self, value):
        if value is None:
            return False
        return bool(value)
        
    def __init__(self, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = False
        super().__init__(**kwargs)

class Date(Field):
    """Date field"""
    def to_mongo(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d')
        return value
        
    def from_mongo(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        return value

class DateTime(Field):
    """DateTime field"""
    def to_mongo(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value
        
    def from_mongo(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return value

class Selection(Field):
    """Selection field"""
    def __init__(self, selection=None, **kwargs):
        super().__init__(**kwargs)
        self.selection = selection or []

class Many2one(Field):
    """Many-to-one relationship field"""
    def __init__(self, comodel_name=None, ondelete='set null', **kwargs):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        self.ondelete = ondelete
        
    def to_mongo(self, value):
        # Store as reference ID
        if value is None:
            return None
        if isinstance(value, dict) and '_id' in value:
            return value['_id']
        return value

class One2many(Field):
    """One-to-many relationship field"""
    def __init__(self, comodel_name=None, inverse_name=None, **kwargs):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        self.inverse_name = inverse_name
        
    def to_mongo(self, value):
        # Store as array of IDs
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return []

class Many2many(Field):
    """Many-to-many relationship field"""
    def __init__(self, comodel_name=None, **kwargs):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        
    def to_mongo(self, value):
        # Store as array of IDs
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return []

# Export fields module
class fields:
    """Field types container (Odoo-style)"""
    Char = Char
    Text = Text
    Integer = Integer
    Float = Float
    Boolean = Boolean
    Date = Date
    DateTime = DateTime
    Selection = Selection
    Many2one = Many2one
    One2many = One2many
    Many2many = Many2many
