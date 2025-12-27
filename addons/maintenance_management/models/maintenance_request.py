"""
Maintenance Request Model
Core model for managing maintenance work orders
"""
from datetime import datetime, timedelta
from core.models import Model
from core.fields import fields

class MaintenanceRequest(Model):
    """Maintenance Request/Work Order"""
    
    _name = 'maintenance_request'
    _description = 'Maintenance Request'
    
    # Reference
    name = fields.Char(string='Reference', required=True, index=True)
    
    # Equipment
    equipment_id = fields.Many2one(
        comodel_name='equipment',
        string='Equipment',
        required=True,
        index=True
    )
    equipment_name = fields.Char(string='Equipment Name')
    equipment_category = fields.Char(string='Equipment Category')
    equipment_location = fields.Char(string='Equipment Location')
    
    # Maintenance Type
    maintenance_type = fields.Selection(
        selection=[
            ('corrective', 'Corrective'),  # Breakdown/Unplanned
            ('preventive', 'Preventive')   # Scheduled/Planned
        ],
        string='Maintenance Type',
        required=True,
        default='corrective',
        index=True
    )
    
    # Priority
    priority = fields.Selection(
        selection=[
            ('0', 'Low'),
            ('1', 'Normal'),
            ('2', 'High'),
            ('3', 'Critical')
        ],
        string='Priority',
        default='1',
        required=True
    )
    
    # Request Details
    request_date = fields.DateTime(
        string='Request Date',
        default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        required=True
    )
    
    description = fields.Text(string='Description', required=True)
    
    # Assignment
    team_id = fields.Many2one(
        comodel_name='maintenance_team',
        string='Maintenance Team',
        required=True,
        index=True
    )
    team_name = fields.Char(string='Team Name')
    
    technician_id = fields.Many2one(
        comodel_name='employee',
        string='Assigned Technician',
        index=True
    )
    technician_name = fields.Char(string='Technician Name')
    
    # Scheduling
    schedule_date = fields.Date(
        string='Scheduled Date',
        required=True,
        index=True
    )
    
    duration = fields.Float(
        string='Estimated Duration (hours)',
        default=2.0
    )
    
    # Execution
    start_date = fields.DateTime(string='Start Date')
    end_date = fields.DateTime(string='End Date')
    actual_duration = fields.Float(string='Actual Duration (hours)')
    
    # State Management
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled')
        ],
        string='Status',
        default='new',
        required=True,
        index=True
    )
    
    # Stage (for Kanban view)
    stage = fields.Selection(
        selection=[
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('repaired', 'Repaired'),
            ('scrap', 'Scrap')
        ],
        string='Stage',
        default='new',
        required=True
    )
    
    # Work Details
    work_done = fields.Text(string='Work Done')
    parts_used = fields.Text(string='Parts Used')
    cost = fields.Float(string='Maintenance Cost')
    
    # Closure
    close_date = fields.DateTime(string='Closure Date')
    closed_by = fields.Char(string='Closed By')
    
    # Computed Fields
    is_overdue = fields.Boolean(string='Overdue', default=False)
    days_overdue = fields.Integer(string='Days Overdue', default=0)
    
    # Color for Kanban
    color = fields.Integer(string='Color Index', default=0)
    
    @classmethod
    def create(cls, vals):
        """Override create to add business logic"""
        # Auto-generate reference number
        if 'name' not in vals or not vals['name']:
            vals['name'] = cls._generate_reference()
        
        # Auto-fill equipment details
        if 'equipment_id' in vals:
            equipment = cls._get_equipment_details(vals['equipment_id'])
            if equipment:
                vals.update({
                    'equipment_name': equipment.get('name'),
                    'equipment_category': equipment.get('category'),
                    'equipment_location': equipment.get('location'),
                    'team_id': equipment.get('maintenance_team_id'),
                    'team_name': equipment.get('maintenance_team_name'),
                    'technician_id': equipment.get('technician_id'),
                    'technician_name': equipment.get('technician_name')
                })
        
        # Set stage based on state
        if 'state' in vals:
            vals['stage'] = vals['state']
        
        # Check if overdue
        if 'schedule_date' in vals:
            vals['is_overdue'] = cls._check_overdue(vals['schedule_date'])
        
        # Set color based on priority
        if 'priority' in vals:
            vals['color'] = cls._get_color_for_priority(vals['priority'])
        
        record = super().create(vals)
        
        # Update equipment status
        if 'equipment_id' in vals and vals.get('state') == 'in_progress':
            cls._update_equipment_status(vals['equipment_id'], 'under_maintenance')
        
        return record
    
    def write(self, vals):
        """Override write to add business logic"""
        # Validate state transition
        if 'state' in vals:
            current_state = self.state if hasattr(self, 'state') else 'new'
            new_state = vals['state']
            
            # Prevent invalid state transitions
            valid_transitions = {
                'new': ['in_progress', 'cancelled'],
                'in_progress': ['done', 'cancelled'],
                'done': [],  # Cannot transition from done
                'cancelled': []  # Cannot transition from cancelled
            }
            
            if current_state in valid_transitions:
                if new_state not in valid_transitions[current_state] and new_state != current_state:
                    # Allow if it's a force update or stage change
                    if 'stage' not in vals:
                        raise ValueError(f"Invalid state transition: {current_state} -> {new_state}")
        
        # State change logic
        if 'state' in vals:
            # Starting work
            if vals['state'] == 'in_progress' and self.state == 'new':
                vals['start_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                vals['stage'] = 'in_progress'
                
                # Update equipment status
                self._update_equipment_status(str(self.equipment_id), 'under_maintenance')
            
            # Completing work
            elif vals['state'] == 'done' and self.state == 'in_progress':
                vals['end_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                vals['close_date'] = vals['end_date']
                vals['stage'] = 'repaired'
                
                # Calculate actual duration
                if self.start_date:
                    start = datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S')
                    end = datetime.now()
                    duration_hours = (end - start).total_seconds() / 3600
                    vals['actual_duration'] = round(duration_hours, 2)
                
                # Update equipment status back to active
                self._update_equipment_status(str(self.equipment_id), 'active')
                
                # Update equipment statistics
                from .equipment import Equipment
                equipment = Equipment.browse([str(self.equipment_id)])
                if equipment:
                    equipment[0].update_maintenance_stats()
        
        # Update stage if provided
        if 'stage' in vals:
            # Map stage to state
            stage_to_state = {
                'new': 'new',
                'in_progress': 'in_progress',
                'repaired': 'done',
                'scrap': 'cancelled'
            }
            
            if vals['stage'] in stage_to_state:
                vals['state'] = stage_to_state[vals['stage']]
            
            # Handle scrap action
            if vals['stage'] == 'scrap':
                from .equipment import Equipment
                equipment = Equipment.browse([str(self.equipment_id)])
                if equipment:
                    equipment[0].action_scrap()
        
        # Check overdue status
        if 'schedule_date' in vals:
            vals['is_overdue'] = self._check_overdue(vals['schedule_date'])
        
        return super().write(vals)
    
    @staticmethod
    def _generate_reference():
        """Generate unique reference number"""
        from datetime import datetime
        import random
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = random.randint(100, 999)
        return f"MNT-{timestamp}-{random_suffix}"
    
    @staticmethod
    def _get_equipment_details(equipment_id):
        """Get equipment details for auto-fill"""
        from .equipment import Equipment
        equipment_list = Equipment.browse([equipment_id])
        if equipment_list:
            return equipment_list[0].read()
        return None
    
    @staticmethod
    def _check_overdue(schedule_date_str):
        """Check if maintenance is overdue"""
        if not schedule_date_str:
            return False
        
        try:
            schedule_date = datetime.strptime(schedule_date_str, '%Y-%m-%d')
            return schedule_date < datetime.now()
        except:
            return False
    
    @staticmethod
    def _get_color_for_priority(priority):
        """Get Kanban color based on priority"""
        color_map = {
            '0': 1,  # Low - Blue
            '1': 0,  # Normal - Default
            '2': 3,  # High - Orange
            '3': 2   # Critical - Red
        }
        return color_map.get(priority, 0)
    
    @staticmethod
    def _update_equipment_status(equipment_id, status):
        """Update equipment status"""
        from .equipment import Equipment
        from bson import ObjectId
        
        # Convert string to ObjectId if needed
        if isinstance(equipment_id, str) and len(equipment_id) == 24:
            try:
                equipment_id = ObjectId(equipment_id)
            except:
                pass
        
        equipment_list = Equipment.browse([equipment_id])
        if equipment_list:
            equipment_list[0].write({'state': status})
    
    def action_start(self):
        """Start maintenance work"""
        self.write({'state': 'in_progress'})
        return True
    
    def action_done(self):
        """Complete maintenance work"""
        self.write({'state': 'done'})
        return True
    
    def action_cancel(self):
        """Cancel maintenance request"""
        self.write({'state': 'cancelled', 'stage': 'scrap'})
        return True
    
    def update_overdue_status(self):
        """Update overdue status and calculate days overdue"""
        if self.state in ['done', 'cancelled']:
            return False
        
        schedule_date = datetime.strptime(self.schedule_date, '%Y-%m-%d')
        today = datetime.now()
        
        if schedule_date < today:
            days_diff = (today - schedule_date).days
            self.write({
                'is_overdue': True,
                'days_overdue': days_diff
            })
            return True
        else:
            self.write({
                'is_overdue': False,
                'days_overdue': 0
            })
            return False
    
    @classmethod
    def check_all_overdue(cls):
        """Check and update overdue status for all active requests"""
        active_requests = cls.search([
            ('state', 'in', ['new', 'in_progress'])
        ])
        
        overdue_count = 0
        for request in active_requests:
            if request.update_overdue_status():
                overdue_count += 1
        
        return overdue_count
