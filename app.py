"""
Flask Application for Maintenance Management System
Implements Odoo-style MVC architecture with MongoDB backend
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core import init_db, get_db
from addons.maintenance_management.models import Equipment, MaintenanceTeam, MaintenanceRequest

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize database
@app.before_request
def before_request():
    """Initialize database connection"""
    init_db()

# ============================================================================
# DASHBOARD & HOME
# ============================================================================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

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
    """API: Get maintenance requests for calendar view (preventive only)"""
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        # Build domain for preventive maintenance
        domain = [('maintenance_type', '=', 'preventive')]
        
        if start_date:
            domain.append(('schedule_date', '>=', start_date))
        if end_date:
            domain.append(('schedule_date', '<=', end_date))
        
        requests = MaintenanceRequest.search(domain=domain)
        
        # Format for calendar
        events = []
        for req in requests:
            data = req.read()
            events.append({
                'id': data['id'],
                'title': f"{data['equipment_name']} - {data['name']}",
                'start': data['schedule_date'],
                'description': data.get('description', ''),
                'technician': data.get('technician_name', ''),
                'state': data['state'],
                'priority': data.get('priority', '1')
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
        
        return jsonify({
            'success': True,
            'data': requests[0].read()
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
                'equipment_by_category': equipment_by_category
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
