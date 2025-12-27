"""
Equipment Model
Tracks all equipment/assets in the organization
"""
from datetime import datetime
from core.models import Model
from core.fields import fields

class Equipment(Model):
    """Equipment/Asset Management"""
    
    _name = 'equipment'
    _description = 'Maintenance Equipment'
    
    # Basic Information
    name = fields.Char(string='Equipment Name', required=True, index=True)
    category = fields.Selection(
        selection=[
            ('machine', 'Machine'),
            ('vehicle', 'Vehicle'),
            ('it_asset', 'IT Asset'),
            ('tool', 'Tool'),
            ('infrastructure', 'Infrastructure')
        ],
        string='Category',
        required=True,
        default='machine'
    )
    
    # Identification
    serial_no = fields.Char(string='Serial Number', index=True)
    model = fields.Char(string='Model')
    manufacturer = fields.Char(string='Manufacturer')
    
    # Assignment
    department_id = fields.Many2one(comodel_name='department', string='Department')
    department_name = fields.Char(string='Department Name')
    
    responsible_id = fields.Many2one(comodel_name='employee', string='Responsible Person')
    responsible_name = fields.Char(string='Responsible Person Name')
    
    # Location
    location = fields.Char(string='Location', required=True)
    
    # Maintenance
    maintenance_team_id = fields.Many2one(
        comodel_name='maintenance_team',
        string='Maintenance Team',
        required=True
    )
    maintenance_team_name = fields.Char(string='Team Name')
    
    technician_id = fields.Many2one(
        comodel_name='technician',
        string='Default Technician'
    )
    technician_name = fields.Char(string='Technician Name')
    
    # Warranty
    warranty_start = fields.Date(string='Warranty Start Date')
    warranty_end = fields.Date(string='Warranty End Date')
    warranty_duration = fields.Integer(string='Warranty Duration (months)')
    
    # Purchase Information
    cost = fields.Float(string='Equipment Cost')
    purchase_date = fields.Date(string='Purchase Date')
    vendor = fields.Char(string='Vendor')
    
    # Status
    state = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('under_maintenance', 'Under Maintenance'),
            ('scrapped', 'Scrapped')
        ],
        string='Status',
        default='active',
        required=True
    )
    
    # Technical Details
    specifications = fields.Text(string='Technical Specifications')
    notes = fields.Text(string='Notes')
    
    # Statistics (computed)
    maintenance_count = fields.Integer(string='Maintenance Count', default=0)
    last_maintenance_date = fields.Date(string='Last Maintenance')
    next_maintenance_date = fields.Date(string='Next Maintenance')
    
    # Preventive Maintenance Schedule
    maintenance_interval = fields.Integer(string='Maintenance Interval (days)', default=90)
    
    @classmethod
    def create(cls, vals):
        """Override create to add business logic"""
        # Auto-generate equipment code if not provided
        if 'name' in vals and 'serial_no' not in vals:
            vals['serial_no'] = cls._generate_serial_no(vals['name'])
                # Ensure unique serial number
        if 'serial_no' in vals:
            existing = cls.search([('serial_no', '=', vals['serial_no'])])
            if existing:
                # Make it unique
                import random
                vals['serial_no'] = f"{vals['serial_no']}-{random.randint(1000, 9999)}"
                # Calculate warranty end date if duration provided
        if 'warranty_start' in vals and 'warranty_duration' in vals:
            from dateutil.relativedelta import relativedelta
            start_date = datetime.strptime(vals['warranty_start'], '%Y-%m-%d')
            vals['warranty_end'] = (start_date + relativedelta(months=vals['warranty_duration'])).strftime('%Y-%m-%d')
        
        return super().create(vals)
    
    def write(self, vals):
        """Override write to add business logic"""
        # Update warranty end date if changed
        if 'warranty_duration' in vals or 'warranty_start' in vals:
            from dateutil.relativedelta import relativedelta
            start_date_str = vals.get('warranty_start', self.warranty_start)
            duration = vals.get('warranty_duration', self.warranty_duration)
            
            if start_date_str and duration:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                vals['warranty_end'] = (start_date + relativedelta(months=duration)).strftime('%Y-%m-%d')
        
        return super().write(vals)
    
    @staticmethod
    def _generate_serial_no(name):
        """Generate serial number based on equipment name"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        prefix = ''.join([c for c in name.upper() if c.isalnum()])[:3]
        return f"{prefix}-{timestamp}"
    
    def action_scrap(self):
        """Mark equipment as scrapped"""
        self.write({'state': 'scrapped'})
        
        # Cancel all pending maintenance requests
        from .maintenance_request import MaintenanceRequest
        from bson import ObjectId
        
        # Try both string and ObjectId formats
        equipment_id_str = str(self._id)
        pending_requests = MaintenanceRequest.search([
            ('equipment_id', '=', equipment_id_str),
            ('state', 'in', ['new', 'in_progress'])
        ])
        
        for request in pending_requests:
            request.write({'state': 'cancelled', 'stage': 'scrap'})
        
        return True
    
    def action_activate(self):
        """Reactivate scrapped equipment"""
        self.write({'state': 'active'})
        return True
    
    def get_maintenance_history(self, limit=10):
        """Get maintenance history for this equipment"""
        from .maintenance_request import MaintenanceRequest
        
        equipment_id_str = str(self._id)
        return MaintenanceRequest.search(
            domain=[('equipment_id', '=', equipment_id_str)],
            order='create_date DESC',
            limit=limit
        )
    
    def update_maintenance_stats(self):
        """Update maintenance statistics"""
        from .maintenance_request import MaintenanceRequest
        
        equipment_id_str = str(self._id)
        
        # Count total maintenance
        count = MaintenanceRequest.search_count([
            ('equipment_id', '=', equipment_id_str),
            ('state', '=', 'done')
        ])
        
        # Get last maintenance date
        last_maintenance = MaintenanceRequest.search(
            domain=[
                ('equipment_id', '=', equipment_id_str),
                ('state', '=', 'done')
            ],
            order='schedule_date DESC',
            limit=1
        )
        
        vals = {'maintenance_count': count}
        
        if last_maintenance:
            last_record = last_maintenance[0]
            vals['last_maintenance_date'] = last_record.schedule_date
            
            # Calculate next maintenance date
            if self.maintenance_interval:
                from dateutil.relativedelta import relativedelta
                last_date = datetime.strptime(last_record.schedule_date, '%Y-%m-%d')
                next_date = last_date + relativedelta(days=self.maintenance_interval)
                vals['next_maintenance_date'] = next_date.strftime('%Y-%m-%d')
        
        self.write(vals)
        return True
