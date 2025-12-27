"""
Maintenance Team Model
Manages teams of technicians specialized in different maintenance types
"""
from core.models import Model
from core.fields import fields

class MaintenanceTeam(Model):
    """Maintenance Team Management"""
    
    _name = 'maintenance_team'
    _description = 'Maintenance Team'
    
    # Basic Information
    name = fields.Char(string='Team Name', required=True, index=True)
    code = fields.Char(string='Team Code', required=True, index=True)
    
    # Specialization
    specialization = fields.Selection(
        selection=[
            ('mechanical', 'Mechanical'),
            ('electrical', 'Electrical'),
            ('it', 'IT/Software'),
            ('civil', 'Civil/Infrastructure'),
            ('general', 'General Maintenance')
        ],
        string='Specialization',
        required=True,
        default='general'
    )
    
    # Team Leader
    team_leader_id = fields.Many2one(
        comodel_name='employee',
        string='Team Leader'
    )
    team_leader_name = fields.Char(string='Team Leader Name')
    
    # Team Members
    member_ids = fields.Many2many(
        comodel_name='employee',
        string='Team Members'
    )
    member_names = fields.Text(string='Member Names (JSON)')
    
    # Contact
    email = fields.Char(string='Team Email')
    phone = fields.Char(string='Team Phone')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    
    # Description
    description = fields.Text(string='Description')
    
    # Statistics
    equipment_count = fields.Integer(string='Equipment Count', default=0)
    active_requests = fields.Integer(string='Active Requests', default=0)
    completed_requests = fields.Integer(string='Completed Requests', default=0)
    
    @classmethod
    def create(cls, vals):
        """Override create to add business logic"""
        # Auto-generate team code if not provided
        if 'name' in vals and 'code' not in vals:
            vals['code'] = cls._generate_team_code(vals['name'])
        
        return super().create(vals)
    
    @staticmethod
    def _generate_team_code(name):
        """Generate team code based on team name"""
        # Take first 3 letters of each word, uppercase
        words = name.split()
        code_parts = []
        for word in words[:3]:
            code_parts.append(word[:3].upper())
        return '-'.join(code_parts)
    
    def get_team_workload(self):
        """Get current workload statistics for the team"""
        from .maintenance_request import MaintenanceRequest
        
        # Active requests
        active = MaintenanceRequest.search_count([
            ('team_id', '=', str(self._id)),
            ('state', 'in', ['new', 'in_progress'])
        ])
        
        # Completed requests
        completed = MaintenanceRequest.search_count([
            ('team_id', '=', str(self._id)),
            ('state', '=', 'done')
        ])
        
        # Update statistics
        self.write({
            'active_requests': active,
            'completed_requests': completed
        })
        
        return {
            'active': active,
            'completed': completed,
            'total': active + completed
        }
    
    def get_available_technicians(self):
        """Get list of available technicians from team members"""
        if not self.member_ids:
            return []
        
        # In real scenario, check technician availability
        # For now, return all team members
        return self.member_ids
    
    def update_equipment_count(self):
        """Update count of equipment assigned to this team"""
        from .equipment import Equipment
        
        count = Equipment.search_count([
            ('maintenance_team_id', '=', str(self._id))
        ])
        
        self.write({'equipment_count': count})
        return count
