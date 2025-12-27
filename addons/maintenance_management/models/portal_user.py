"""
Portal User Model
Manages user authentication and portal access
"""
from core.models import Model
from core.fields import fields
from datetime import datetime, timedelta
import bcrypt

class PortalUser(Model):
    """Portal User Management - Authentication & Access Control"""
    
    _name = 'portal_user'
    _description = 'Portal User'
    
    # Basic Information
    name = fields.Char(string='Full Name', required=True, index=True)
    email = fields.Char(string='Email', required=True, index=True)
    password_hash = fields.Char(string='Password Hash', required=True)
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    is_admin = fields.Boolean(string='Is Administrator', default=False)
    
    # Security
    last_login = fields.DateTime(string='Last Login')
    login_attempts = fields.Integer(string='Failed Login Attempts', default=0)
    locked_until = fields.DateTime(string='Locked Until')
    
    # Audit
    create_date = fields.DateTime(string='Created On', default=lambda: datetime.now())
    write_date = fields.DateTime(string='Last Updated', default=lambda: datetime.now())
    
    @classmethod
    def create(cls, vals):
        """Create user with password hashing"""
        # Hash password before storing
        if 'password' in vals:
            vals['password_hash'] = cls.hash_password(vals['password'])
            del vals['password']  # Remove plain password
        
        # Set default values
        if 'active' not in vals:
            vals['active'] = True
        if 'is_admin' not in vals:
            vals['is_admin'] = False
        if 'login_attempts' not in vals:
            vals['login_attempts'] = 0
        
        # Ensure email is lowercase
        if 'email' in vals:
            vals['email'] = vals['email'].lower().strip()
        
        return super().create(vals)
    
    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password, hashed_password):
        """Verify password against hash"""
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    @classmethod
    def authenticate(cls, email, password):
        """
        Authenticate user with email and password
        Returns: (success: bool, user: PortalUser|None, error: str|None)
        """
        # Normalize email
        email = email.lower().strip()
        
        # Find user by email
        users = cls.search([('email', '=', email), ('active', '=', True)])
        
        if not users:
            return False, None, "Account not exist"
        
        user = users[0]
        user_data = user.read()
        
        # Check if account is locked
        if user_data.get('locked_until'):
            locked_until = user_data['locked_until']
            if isinstance(locked_until, str):
                locked_until = datetime.fromisoformat(locked_until)
            if datetime.now() < locked_until:
                return False, None, "Account temporarily locked. Try again later."
        
        # Verify password
        if not cls.verify_password(password, user_data['password_hash']):
            # Increment failed attempts
            attempts = user_data.get('login_attempts', 0) + 1
            update_vals = {'login_attempts': attempts}
            
            # Lock account after 5 failed attempts
            if attempts >= 5:
                update_vals['locked_until'] = datetime.now() + timedelta(minutes=15)
            
            user.write(update_vals)
            return False, None, "Invalid Password"
        
        # Successful login - reset attempts and update last login
        user.write({
            'login_attempts': 0,
            'locked_until': None,
            'last_login': datetime.now()
        })
        
        return True, user, None
    
    @classmethod
    def validate_password_strength(cls, password):
        """
        Validate password meets security requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one special character
        Returns: (valid: bool, error: str|None)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not has_upper:
            return False, "Password must contain at least one uppercase letter"
        if not has_lower:
            return False, "Password must contain at least one lowercase letter"
        if not has_special:
            return False, "Password must contain at least one special character"
        
        return True, None
    
    @classmethod
    def email_exists(cls, email):
        """Check if email already exists"""
        email = email.lower().strip()
        count = cls.search_count([('email', '=', email)])
        return count > 0
