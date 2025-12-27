"""
Flask Application for Maintenance Management System
Implements Odoo-style MVC architecture with MongoDB backend
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core import init_db, get_db
from addons.maintenance_management.models import Equipment, MaintenanceTeam, MaintenanceRequest, PortalUser

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY  # Required for Flask-Login sessions
CORS(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth_signin'  # Redirect to sign in page
login_manager.login_message = None  # Disable flash messages (non-Odoo style)

# User class for Flask-Login
class User(UserMixin):
    """User session object"""
    def __init__(self, user_data):
        self.id = user_data['id']
        self.name = user_data['name']
        self.email = user_data['email']
        self.is_admin = user_data.get('is_admin', False)

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user from database by ID"""
    try:
        users = PortalUser.browse([user_id])
        if users:
            user_data = users[0].read()
            return User(user_data)
        return None
    except:
        return None

# Initialize database
@app.before_request
def before_request():
    """Initialize database connection and enforce authentication"""
    init_db()
    
    # List of public routes that don't require authentication
    public_routes = [
        'auth_signin',
        'auth_signup',
        'auth_forgot_password',
        'api_signin',
        'api_signup',
        'api_forgot_password',
        'static'
    ]
    
    # Check if current endpoint requires authentication
    if request.endpoint and request.endpoint not in public_routes:
        if not current_user.is_authenticated:
            # Redirect to login page for unauthenticated users
            return redirect(url_for('auth_signin'))

# ============================================================================
# DASHBOARD & HOME
# ============================================================================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/favicon.ico')
def favicon():
    """Serve favicon or return 204 No Content to prevent console errors"""
    # Return 204 No Content - tells browser there's no favicon without error
    return '', 204

@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools():
    """Handle Chrome DevTools well-known request"""
    # Return 204 No Content to prevent 404 errors when DevTools is open
    return '', 204

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Equipment stats
        total_equipment = Equipment.search_count([])
        active_equipment = Equipment.search_count([('state', '=', 'active')])
        under_maintenance = Equipment.search_count([('state', '=', 'under_maintenance')])
        scrapped_equipment = Equipment.search_count([('state', '=', 'scrapped')])
        
        # Maintenance request stats
        total_requests = MaintenanceRequest.search_count([])
        new_requests = MaintenanceRequest.search_count([('state', '=', 'new')])
        in_progress_requests = MaintenanceRequest.search_count([('state', '=', 'in_progress')])
        completed_requests = MaintenanceRequest.search_count([('state', '=', 'done')])
        
        # Overdue requests
        overdue_requests = MaintenanceRequest.search_count([
            ('is_overdue', '=', True),
            ('state', 'in', ['new', 'in_progress'])
        ])
        
        # Team stats
        total_teams = MaintenanceTeam.search_count([('active', '=', True)])
        
        # Maintenance by type
        corrective_count = MaintenanceRequest.search_count([('maintenance_type', '=', 'corrective')])
        preventive_count = MaintenanceRequest.search_count([('maintenance_type', '=', 'preventive')])
        
        return jsonify({
            'success': True,
            'data': {
                'equipment': {
                    'total': total_equipment,
                    'active': active_equipment,
                    'under_maintenance': under_maintenance,
                    'scrapped': scrapped_equipment
                },
                'requests': {
                    'total': total_requests,
                    'new': new_requests,
                    'in_progress': in_progress_requests,
                    'completed': completed_requests,
                    'overdue': overdue_requests
                },
                'teams': {
                    'total': total_teams
                },
                'maintenance_types': {
                    'corrective': corrective_count,
                    'preventive': preventive_count
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# EQUIPMENT ROUTES
# ============================================================================

@app.route('/equipment')
def equipment_list():
    """Equipment list view (Tree view)"""
    return render_template('equipment/list.html')

@app.route('/equipment/form')
@app.route('/equipment/form/<equipment_id>')
def equipment_form(equipment_id=None):
    """Equipment form view"""
    return render_template('equipment/form.html', equipment_id=equipment_id)

@app.route('/api/equipment', methods=['GET'])
def get_equipment_list():
    """API: Get equipment list"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 80, type=int)
        offset = request.args.get('offset', 0, type=int)
        state = request.args.get('state')
        category = request.args.get('category')
        search = request.args.get('search')
        
        # Build domain
        domain = []
        if state:
            domain.append(('state', '=', state))
        if category:
            domain.append(('category', '=', category))
        if search:
            domain.append(('name', 'like', search))
        
        # Search equipment
        equipment_list = Equipment.search(domain=domain, limit=limit, offset=offset)
        total_count = Equipment.search_count(domain=domain)
        
        # Format results
        records = [eq.read() for eq in equipment_list]
        
        return jsonify({
            'success': True,
            'data': records,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/equipment/<equipment_id>', methods=['GET'])
def get_equipment(equipment_id):
    """API: Get single equipment"""
    try:
        equipment_list = Equipment.browse([equipment_id])
        if not equipment_list:
            return jsonify({'success': False, 'error': 'Equipment not found'}), 404
        
        equipment = equipment_list[0]
        data = equipment.read()
        
        # Get maintenance history
        history = equipment.get_maintenance_history(limit=10)
        data['maintenance_history'] = [req.read() for req in history]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/equipment', methods=['POST'])
def create_equipment():
    """API: Create equipment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'category', 'location', 'maintenance_team_id']
        missing_fields = [f for f in required_fields if f not in data or not data[f]]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        equipment = Equipment.create(data)
        
        return jsonify({
            'success': True,
            'data': equipment.read(),
            'message': 'Equipment created successfully'
        }), 201
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/equipment/<equipment_id>', methods=['PUT'])
def update_equipment(equipment_id):
    """API: Update equipment"""
    try:
        equipment_list = Equipment.browse([equipment_id])
        if not equipment_list:
            return jsonify({'success': False, 'error': 'Equipment not found'}), 404
        
        equipment = equipment_list[0]
        data = request.get_json()
        equipment.write(data)
        
        return jsonify({
            'success': True,
            'data': equipment.read(),
            'message': 'Equipment updated successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/equipment/<equipment_id>', methods=['DELETE'])
def delete_equipment(equipment_id):
    """API: Delete equipment"""
    try:
        equipment_list = Equipment.browse([equipment_id])
        if not equipment_list:
            return jsonify({'success': False, 'error': 'Equipment not found'}), 404
        
        equipment = equipment_list[0]
        equipment.unlink()
        
        return jsonify({
            'success': True,
            'message': 'Equipment deleted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/equipment/<equipment_id>/scrap', methods=['POST'])
def scrap_equipment(equipment_id):
    """API: Scrap equipment"""
    try:
        equipment_list = Equipment.browse([equipment_id])
        if not equipment_list:
            return jsonify({'success': False, 'error': 'Equipment not found'}), 404
        
        equipment = equipment_list[0]
        equipment.action_scrap()
        
        return jsonify({
            'success': True,
            'message': 'Equipment marked as scrapped'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# PORTAL USER ROUTES
# ============================================================================

@app.route('/api/portal-users', methods=['GET'])
def list_portal_users():
    """API: List all portal users (for team member selection)"""
    try:
        users = PortalUser.search([('active', '=', True)])
        return jsonify({
            'success': True,
            'data': [user.read() for user in users]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# MAINTENANCE TEAM ROUTES
# ============================================================================

@app.route('/teams')
def team_list():
    """Team list view"""
    return render_template('teams/list.html')

@app.route('/api/teams', methods=['GET'])
def get_team_list():
    """API: Get team list"""
    try:
        teams = MaintenanceTeam.search([('active', '=', True)])
        records = [team.read() for team in teams]
        
        return jsonify({
            'success': True,
            'data': records,
            'total': len(records)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/teams', methods=['POST'])
def create_team():
    """API: Create team"""
    try:
        data = request.get_json()
        team = MaintenanceTeam.create(data)
        
        return jsonify({
            'success': True,
            'data': team.read(),
            'message': 'Team created successfully'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/teams/<team_id>', methods=['PUT'])
def update_team(team_id):
    """API: Update team"""
    try:
        data = request.get_json()
        team = MaintenanceTeam.browse([team_id])
        
        if not team:
            return jsonify({'success': False, 'error': 'Team not found'}), 404
        
        team.write(data)
        
        return jsonify({
            'success': True,
            'data': team.read(),
            'message': 'Team updated successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/teams/<team_id>', methods=['DELETE'])
def delete_team(team_id):
    """API: Delete team"""
    try:
        team = MaintenanceTeam.browse([team_id])
        
        if not team:
            return jsonify({'success': False, 'error': 'Team not found'}), 404
        
        # Check if team has active maintenance requests
        active_requests = MaintenanceRequest.search_count([
            ('team_id', '=', team_id),
            ('state', 'in', ['new', 'in_progress'])
        ])
        
        if active_requests > 0:
            return jsonify({
                'success': False, 
                'error': f'Cannot delete team with {active_requests} active maintenance requests'
            }), 400
        
        team.unlink()
        
        return jsonify({
            'success': True,
            'message': 'Team deleted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# MAINTENANCE REQUEST ROUTES
# ============================================================================

@app.route('/maintenance')
def maintenance_list():
    """Maintenance request list view"""
    return render_template('maintenance/list.html')

@app.route('/maintenance/kanban')
def maintenance_kanban():
    """Maintenance request Kanban view"""
    return render_template('maintenance/kanban.html')

@app.route('/maintenance/calendar')
def maintenance_calendar():
    """Maintenance request calendar view"""
    return render_template('maintenance/calendar.html')

@app.route('/maintenance/form')
@app.route('/maintenance/form/<request_id>')
def maintenance_form(request_id=None):
    """Maintenance request form view"""
    return render_template('maintenance/form.html', request_id=request_id)

@app.route('/api/maintenance', methods=['GET'])
def get_maintenance_list():
    """API: Get maintenance request list"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 80, type=int)
        offset = request.args.get('offset', 0, type=int)
        state = request.args.get('state')
        maintenance_type = request.args.get('maintenance_type')
        equipment_id = request.args.get('equipment_id')
        team_id = request.args.get('team_id')
        priority = request.args.get('priority')
        is_overdue = request.args.get('is_overdue')
        search = request.args.get('search')
        
        # Build domain
        domain = []
        if state:
            domain.append(('state', '=', state))
        if maintenance_type:
            domain.append(('maintenance_type', '=', maintenance_type))
        if equipment_id:
            domain.append(('equipment_id', '=', equipment_id))
        if team_id:
            domain.append(('team_id', '=', team_id))
        if priority:
            domain.append(('priority', '=', priority))
        if is_overdue == 'true':
            domain.append(('is_overdue', '=', True))
        elif is_overdue == 'false':
            domain.append(('is_overdue', '=', False))
        if search:
            domain.append(('name', 'like', search))
        
        # Search requests
        requests = MaintenanceRequest.search(
            domain=domain,
            limit=limit,
            offset=offset,
            order='schedule_date DESC'
        )
        total_count = MaintenanceRequest.search_count(domain=domain)
        
        # Format results
        records = [req.read() for req in requests]
        
        return jsonify({
            'success': True,
            'data': records,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/kanban', methods=['GET'])
def get_maintenance_kanban():
    """API: Get maintenance requests for Kanban view"""
    try:
        # Get all active requests
        requests = MaintenanceRequest.search([
            ('state', 'in', ['new', 'in_progress', 'done'])
        ])
        
        # Group by stage
        kanban_data = {
            'new': [],
            'in_progress': [],
            'repaired': [],
            'scrap': []
        }
        
        for req in requests:
            data = req.read()
            stage = data.get('stage', 'new')
            if stage in kanban_data:
                kanban_data[stage].append(data)
        
        return jsonify({
            'success': True,
            'data': kanban_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/calendar', methods=['GET'])
def get_maintenance_calendar():
    """API: Get maintenance requests for calendar view (all types)"""
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        maintenance_type = request.args.get('type')  # New: support type filtering
        
        # Build domain - support all types by default
        domain = []
        
        # Optional type filter
        if maintenance_type and maintenance_type in ['corrective', 'preventive']:
            domain.append(('maintenance_type', '=', maintenance_type))
        
        if start_date:
            domain.append(('schedule_date', '>=', start_date))
        if end_date:
            domain.append(('schedule_date', '<=', end_date))
        
        requests = MaintenanceRequest.search(domain=domain)
        
        # Format for calendar
        events = []
        for req in requests:
            data = req.read()
            
            # Determine event color based on type and state
            if data['state'] == 'done':
                color = '#6c757d'  # gray - completed
            elif data.get('is_overdue'):
                color = '#dc3545'  # red - overdue
            elif data['maintenance_type'] == 'preventive':
                color = '#28a745'  # green - preventive
            else:
                color = '#ffc107'  # yellow - corrective
            
            events.append({
                'id': data['id'],
                'title': f"{data['equipment_name']} - {data['name']}",
                'start': data['schedule_date'],
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'id': data['id'],
                    'maintenance_type': data['maintenance_type'],
                    'equipment': data.get('equipment_name', 'N/A'),
                    'location': data.get('equipment_location', 'N/A'),
                    'description': data.get('description', ''),
                    'technician': data.get('technician_name', 'Unassigned'),
                    'team': data.get('team_name', 'N/A'),
                    'state': data['state'],
                    'priority': data.get('priority', '1'),
                    'duration': data.get('duration', 0)
                }
            })
        
        return jsonify({
            'success': True,
            'data': events
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance', methods=['POST'])
def create_maintenance_request():
    """API: Create maintenance request"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['equipment_id', 'maintenance_type', 'description', 'schedule_date']
        missing_fields = [f for f in required_fields if f not in data or not data[f]]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Validate equipment exists
        equipment = Equipment.browse([data['equipment_id']])
        if not equipment:
            return jsonify({
                'success': False,
                'error': 'Equipment not found'
            }), 404
        
        # Check equipment is not scrapped
        if equipment[0].state == 'scrapped':
            return jsonify({
                'success': False,
                'error': 'Cannot create maintenance request for scrapped equipment'
            }), 400
        
        maintenance_request = MaintenanceRequest.create(data)
        
        return jsonify({
            'success': True,
            'data': maintenance_request.read(),
            'message': 'Maintenance request created successfully'
        }), 201
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/maintenance/<request_id>', methods=['GET'])
def get_maintenance_request(request_id):
    """API: Get single maintenance request"""
    try:
        requests = MaintenanceRequest.browse([request_id])
        if not requests:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        data = requests[0].read()
        
        # Auto-populate missing equipment department from equipment record
        if data.get('equipment_id') and not data.get('equipment_department'):
            equipment_list = Equipment.browse([data['equipment_id']])
            if equipment_list:
                equipment_data = equipment_list[0].read()
                data['equipment_department'] = equipment_data.get('department_name', '')
                # Also update other missing equipment fields
                if not data.get('equipment_name'):
                    data['equipment_name'] = equipment_data.get('name', '')
                if not data.get('equipment_category'):
                    data['equipment_category'] = equipment_data.get('category', '')
                if not data.get('equipment_location'):
                    data['equipment_location'] = equipment_data.get('location', '')
                
                # Update the record in database to include this data
                requests[0].write({
                    'equipment_department': data['equipment_department'],
                    'equipment_name': data.get('equipment_name'),
                    'equipment_category': data.get('equipment_category'),
                    'equipment_location': data.get('equipment_location')
                })
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance/<request_id>', methods=['PUT'])
def update_maintenance_request(request_id):
    """API: Update maintenance request"""
    try:
        requests = MaintenanceRequest.browse([request_id])
        if not requests:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        maintenance_request = requests[0]
        data = request.get_json()
        maintenance_request.write(data)
        
        return jsonify({
            'success': True,
            'data': maintenance_request.read(),
            'message': 'Request updated successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/maintenance/<request_id>/start', methods=['POST'])
def start_maintenance(request_id):
    """API: Start maintenance work"""
    try:
        requests = MaintenanceRequest.browse([request_id])
        if not requests:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        maintenance_request = requests[0]
        maintenance_request.action_start()
        
        return jsonify({
            'success': True,
            'data': maintenance_request.read(),
            'message': 'Maintenance started'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/maintenance/<request_id>/done', methods=['POST'])
def complete_maintenance(request_id):
    """API: Complete maintenance work"""
    try:
        requests = MaintenanceRequest.browse([request_id])
        if not requests:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        maintenance_request = requests[0]
        maintenance_request.action_done()
        
        return jsonify({
            'success': True,
            'data': maintenance_request.read(),
            'message': 'Maintenance completed'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/maintenance/<request_id>/state', methods=['POST'])
def change_maintenance_state(request_id):
    """API: Change maintenance request state (universal state transition endpoint)"""
    try:
        print(f"[STATE CHANGE] Request ID: {request_id}")
        requests = MaintenanceRequest.browse([request_id])
        if not requests:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        data = request.get_json()
        new_state = data.get('state')
        print(f"[STATE CHANGE] New state: {new_state}")
        
        if not new_state:
            return jsonify({'success': False, 'error': 'State is required'}), 400
        
        # Validate state
        valid_states = ['new', 'in_progress', 'done', 'cancelled']
        if new_state not in valid_states:
            return jsonify({'success': False, 'error': f'Invalid state. Must be one of: {", ".join(valid_states)}'}), 400
        
        maintenance_request = requests[0]
        print(f"[STATE CHANGE] Current state: {maintenance_request.state}")
        
        # Call appropriate action method based on state
        if new_state == 'in_progress':
            maintenance_request.action_start()
            message = 'Maintenance work started'
        elif new_state == 'done':
            maintenance_request.action_done()
            message = 'Maintenance completed'
        elif new_state == 'cancelled':
            print("[STATE CHANGE] Calling action_cancel()...")
            maintenance_request.action_cancel()
            print("[STATE CHANGE] action_cancel() completed")
            message = 'Maintenance request cancelled'
        else:
            # Direct state change for 'new' or other states
            maintenance_request.write({'state': new_state})
            message = f'State changed to {new_state}'
        
        print(f"[STATE CHANGE] Success! New state: {maintenance_request.state}")
        print(f"[STATE CHANGE] Success! New state: {maintenance_request.state}")
        return jsonify({
            'success': True,
            'data': maintenance_request.read(),
            'message': message
        })
    except Exception as e:
        print(f"[STATE CHANGE ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# REPORTS & ANALYTICS
# ============================================================================

@app.route('/reports')
def reports():
    """Reports dashboard"""
    return render_template('reports/dashboard.html')

@app.route('/api/reports/pivot')
def get_pivot_data():
    """API: Get pivot table data"""
    try:
        # Get all maintenance requests
        requests = MaintenanceRequest.search([])
        
        # Prepare pivot data
        pivot_data = []
        for req in requests:
            data = req.read()
            pivot_data.append({
                'name': data.get('name', ''),
                'equipment_name': data.get('equipment_name', ''),
                'equipment_category': data.get('equipment_category', ''),
                'team_name': data.get('team_name', ''),
                'maintenance_type': data.get('maintenance_type', ''),
                'state': data.get('state', ''),
                'priority': data.get('priority', '1'),
                'duration': data.get('actual_duration', data.get('duration', 0)),
                'cost': data.get('cost', 0),
                'schedule_date': data.get('schedule_date', ''),
                'is_overdue': data.get('is_overdue', False)
            })
        
        return jsonify({
            'success': True,
            'data': pivot_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/charts')
def get_chart_data():
    """API: Get data for charts"""
    try:
        # Maintenance by type
        corrective = MaintenanceRequest.search_count([('maintenance_type', '=', 'corrective')])
        preventive = MaintenanceRequest.search_count([('maintenance_type', '=', 'preventive')])
        
        # Maintenance by state
        new = MaintenanceRequest.search_count([('state', '=', 'new')])
        in_progress = MaintenanceRequest.search_count([('state', '=', 'in_progress')])
        done = MaintenanceRequest.search_count([('state', '=', 'done')])
        cancelled = MaintenanceRequest.search_count([('state', '=', 'cancelled')])
        
        # Equipment by category
        equipment_by_category = {}
        categories = ['machine', 'vehicle', 'it_asset', 'tool', 'infrastructure']
        for cat in categories:
            count = Equipment.search_count([('category', '=', cat)])
            if count > 0:
                equipment_by_category[cat] = count
        
        # Team workload - count maintenance requests per team
        teams = MaintenanceTeam.search([('active', '=', True)])
        team_workload = {}
        for team in teams:
            team_data = team.read()
            active_count = MaintenanceRequest.search_count([
                ('team_id', '=', team_data['id']),
                ('state', 'in', ['new', 'in_progress'])
            ])
            if active_count > 0:
                team_workload[team_data['name']] = active_count
        
        return jsonify({
            'success': True,
            'data': {
                'maintenance_by_type': {
                    'corrective': corrective,
                    'preventive': preventive
                },
                'maintenance_by_state': {
                    'new': new,
                    'in_progress': in_progress,
                    'done': done,
                    'cancelled': cancelled
                },
                'equipment_by_category': equipment_by_category,
                'team_workload': team_workload,
                'teams': {
                    'total': len(teams),
                    'workload': team_workload
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/auth/signin')
def auth_signin():
    """Sign In page"""
    return render_template('auth/signin.html')

@app.route('/auth/signup')
def auth_signup():
    """Sign Up page"""
    return render_template('auth/signup.html')

@app.route('/auth/forgot-password')
def auth_forgot_password():
    """Forgot Password page"""
    return render_template('auth/forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    """Logout and clear session"""
    logout_user()
    session.clear()
    return redirect(url_for('auth_signin'))

@app.route('/api/auth/signin', methods=['POST'])
def api_signin():
    """API: Sign In authentication with MongoDB validation"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate required fields
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Authenticate user
        success, user, error = PortalUser.authenticate(email, password)
        
        if not success:
            return jsonify({
                'success': False,
                'error': error
            }), 401
        
        # Successful login - Create session with Flask-Login
        user_data = user.read()
        user_obj = User(user_data)
        login_user(user_obj, remember=False)
        
        return jsonify({
            'success': True,
            'message': 'Sign in successful',
            'user': {
                'id': user_data['id'],
                'name': user_data['name'],
                'email': user_data['email']
            },
            'redirect': '/'
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    """API: Sign Up - Create new portal user with validation"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate required fields
        if not name or not email or not password:
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Check if email already exists (duplicate prevention)
        if PortalUser.email_exists(email):
            return jsonify({
                'success': False,
                'error': 'Email Id should not be a duplicate in database'
            }), 400
        
        # Validate password strength
        valid, error_msg = PortalUser.validate_password_strength(password)
        if not valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Create portal user in MongoDB
        user = PortalUser.create({
            'name': name,
            'email': email,
            'password': password,  # Will be hashed in create method
            'active': True
        })
        
        # Auto-login after successful registration
        user_data = user.read()
        user_obj = User(user_data)
        login_user(user_obj, remember=False)
        
        # Success - redirect to dashboard
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'redirect': '/'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    """API: Forgot Password - Send reset link"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400
        
        # Check if user exists (but don't reveal this to prevent email enumeration)
        user_exists = PortalUser.email_exists(email)
        
        # TODO: In production, implement:
        # 1. Generate secure reset token
        # 2. Store token with expiration in database
        # 3. Send email with reset link
        # 4. Implement reset password page
        
        # Always return success for security (prevent email enumeration)
        return jsonify({
            'success': True,
            'message': 'If an account exists, a reset link has been sent'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@app.route('/api/check_overdue', methods=['POST'])
def check_overdue():
    """API: Check and update overdue requests"""
    try:
        overdue_count = MaintenanceRequest.check_all_overdue()
        
        return jsonify({
            'success': True,
            'overdue_count': overdue_count,
            'message': f'{overdue_count} overdue requests updated'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 MAINTENANCE MANAGEMENT SYSTEM")
    print("=" * 60)
    print(f"📡 Starting server on http://{Config.HOST}:{Config.PORT}")
    print(f"🔗 MongoDB URI: {Config.MONGO_URI}")
    print(f"💾 Database: {Config.MONGO_DB_NAME}")
    print("=" * 60)
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    print("✓ Server ready!")
    print("=" * 60)
    
    # Windows-safe configuration to prevent WinError 10038
    # Use stat reloader instead of watchdog to avoid socket threading issues
    app.run(
        host=Config.HOST, 
        port=Config.PORT, 
        debug=Config.DEBUG,
        use_reloader=True,
        reloader_type='stat',  # Use stat instead of watchdog (Windows-safe)
        threaded=True
    )
