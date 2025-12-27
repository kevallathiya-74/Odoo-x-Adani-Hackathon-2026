"""
Data Seeder - Creates real initial data for the system
NO MOCK DATA - All data is created through proper ORM methods
"""
import sys
from datetime import datetime, timedelta
from core import init_db
from addons.maintenance_management.models import Equipment, MaintenanceTeam, MaintenanceRequest

def seed_maintenance_teams():
    """Create maintenance teams"""
    print("\n📋 Creating Maintenance Teams...")
    
    teams_data = [
        {
            'name': 'Mechanical Maintenance Team',
            'code': 'MEC-TEAM',
            'specialization': 'mechanical',
            'team_leader_name': 'Rajesh Kumar',
            'email': 'mechanical@adani.com',
            'phone': '+91-9876543210',
            'description': 'Handles all mechanical equipment maintenance including heavy machinery',
            'member_ids': [],
            'active': True
        },
        {
            'name': 'Electrical Maintenance Team',
            'code': 'ELE-TEAM',
            'specialization': 'electrical',
            'team_leader_name': 'Priya Sharma',
            'email': 'electrical@adani.com',
            'phone': '+91-9876543211',
            'description': 'Responsible for electrical systems and power equipment',
            'member_ids': [],
            'active': True
        },
        {
            'name': 'IT & Software Team',
            'code': 'IT-TEAM',
            'specialization': 'it',
            'team_leader_name': 'Amit Patel',
            'email': 'it@adani.com',
            'phone': '+91-9876543212',
            'description': 'Manages IT assets, servers, and software systems',
            'member_ids': [],
            'active': True
        },
        {
            'name': 'Civil Infrastructure Team',
            'code': 'CIV-TEAM',
            'specialization': 'civil',
            'team_leader_name': 'Suresh Reddy',
            'email': 'civil@adani.com',
            'phone': '+91-9876543213',
            'description': 'Maintains buildings, roads, and infrastructure',
            'member_ids': [],
            'active': True
        }
    ]
    
    created_teams = []
    for team_data in teams_data:
        team = MaintenanceTeam.create(team_data)
        created_teams.append(team)
        print(f"  ✓ Created team: {team.name} ({team.code})")
    
    print(f"✅ Created {len(created_teams)} maintenance teams")
    return created_teams

def seed_equipment(teams):
    """Create equipment"""
    print("\n🔧 Creating Equipment...")
    
    # Get team IDs for reference
    mech_team = teams[0]
    elec_team = teams[1]
    it_team = teams[2]
    civil_team = teams[3]
    
    equipment_data = [
        # Mechanical Equipment
        {
            'name': 'Hydraulic Press Machine HP-2000',
            'category': 'machine',
            'serial_no': 'HP2K-20240101',
            'model': 'HP-2000X',
            'manufacturer': 'Adani Manufacturing',
            'department_name': 'Production',
            'responsible_name': 'Vikram Singh',
            'location': 'Factory Floor - Section A',
            'maintenance_team_id': str(mech_team._id),
            'maintenance_team_name': mech_team.name,
            'technician_name': 'Ravi Kumar',
            'warranty_start': '2023-01-15',
            'warranty_duration': 24,
            'cost': 5500000.00,
            'purchase_date': '2023-01-10',
            'vendor': 'Industrial Equipment Ltd',
            'state': 'active',
            'specifications': 'Capacity: 2000 tons, Power: 150 HP, Working pressure: 350 bar',
            'maintenance_interval': 90
        },
        {
            'name': 'CNC Milling Machine M-350',
            'category': 'machine',
            'serial_no': 'CNC-M350-2023',
            'model': 'M-350 Pro',
            'manufacturer': 'Precision Tools Inc',
            'department_name': 'Production',
            'responsible_name': 'Anita Desai',
            'location': 'Factory Floor - Section B',
            'maintenance_team_id': str(mech_team._id),
            'maintenance_team_name': mech_team.name,
            'technician_name': 'Sunil Yadav',
            'warranty_start': '2023-06-20',
            'warranty_duration': 36,
            'cost': 8500000.00,
            'purchase_date': '2023-06-15',
            'vendor': 'Precision Tools Inc',
            'state': 'active',
            'specifications': '3-axis CNC, Spindle speed: 10000 RPM, Working area: 350x250x200mm',
            'maintenance_interval': 60
        },
        # Vehicles
        {
            'name': 'Forklift Truck FL-25',
            'category': 'vehicle',
            'serial_no': 'FLT-25-2022',
            'model': 'FL-25HD',
            'manufacturer': 'Toyota Material Handling',
            'department_name': 'Logistics',
            'responsible_name': 'Mahesh Gupta',
            'location': 'Warehouse - Bay 3',
            'maintenance_team_id': str(mech_team._id),
            'maintenance_team_name': mech_team.name,
            'technician_name': 'Ramesh Patil',
            'warranty_start': '2022-08-10',
            'warranty_duration': 12,
            'cost': 1200000.00,
            'purchase_date': '2022-08-05',
            'vendor': 'Toyota Material Handling India',
            'state': 'active',
            'specifications': 'Load capacity: 2.5 tons, Diesel engine, Fork length: 1200mm',
            'maintenance_interval': 30
        },
        # Electrical Equipment
        {
            'name': 'Transformer TR-500KVA',
            'category': 'infrastructure',
            'serial_no': 'TR-500-2021',
            'model': 'TR-500KVA',
            'manufacturer': 'ABB India',
            'department_name': 'Electrical',
            'responsible_name': 'Deepak Joshi',
            'location': 'Electrical Substation - Block A',
            'maintenance_team_id': str(elec_team._id),
            'maintenance_team_name': elec_team.name,
            'technician_name': 'Anil Verma',
            'warranty_start': '2021-03-15',
            'warranty_duration': 60,
            'cost': 3500000.00,
            'purchase_date': '2021-03-10',
            'vendor': 'ABB India Ltd',
            'state': 'active',
            'specifications': 'Rating: 500KVA, Primary: 11KV, Secondary: 415V, Oil-cooled',
            'maintenance_interval': 180
        },
        {
            'name': 'Diesel Generator DG-250KVA',
            'category': 'machine',
            'serial_no': 'DG-250-2022',
            'model': 'DG-250-Silent',
            'manufacturer': 'Cummins India',
            'department_name': 'Electrical',
            'responsible_name': 'Sanjay Kulkarni',
            'location': 'DG Room - Building B',
            'maintenance_team_id': str(elec_team._id),
            'maintenance_team_name': elec_team.name,
            'technician_name': 'Vijay Deshmukh',
            'warranty_start': '2022-11-01',
            'warranty_duration': 24,
            'cost': 2800000.00,
            'purchase_date': '2022-10-28',
            'vendor': 'Cummins India Ltd',
            'state': 'active',
            'specifications': 'Capacity: 250KVA, Fuel: Diesel, Sound level: 65dB, Auto-start',
            'maintenance_interval': 90
        },
        # IT Assets
        {
            'name': 'Server Dell PowerEdge R740',
            'category': 'it_asset',
            'serial_no': 'DL-R740-2023001',
            'model': 'PowerEdge R740',
            'manufacturer': 'Dell Technologies',
            'department_name': 'IT',
            'responsible_name': 'Rahul Mehta',
            'location': 'Data Center - Rack A-05',
            'maintenance_team_id': str(it_team._id),
            'maintenance_team_name': it_team.name,
            'technician_name': 'Kiran Bhat',
            'warranty_start': '2023-04-01',
            'warranty_duration': 36,
            'cost': 850000.00,
            'purchase_date': '2023-03-25',
            'vendor': 'Dell Technologies India',
            'state': 'active',
            'specifications': '2x Intel Xeon, 128GB RAM, 4TB SSD RAID, Dual PSU',
            'maintenance_interval': 120
        },
        {
            'name': 'Network Switch Cisco Catalyst 9300',
            'category': 'it_asset',
            'serial_no': 'CS-9300-2023',
            'model': 'Catalyst 9300-48P',
            'manufacturer': 'Cisco Systems',
            'department_name': 'IT',
            'responsible_name': 'Neha arawak',
            'location': 'Data Center - Rack B-03',
            'maintenance_team_id': str(it_team._id),
            'maintenance_team_name': it_team.name,
            'technician_name': 'Prakash Nair',
            'warranty_start': '2023-02-15',
            'warranty_duration': 60,
            'cost': 450000.00,
            'purchase_date': '2023-02-10',
            'vendor': 'Cisco Systems India',
            'state': 'active',
            'specifications': '48-port PoE+, 10G uplinks, Stackable, Layer 3 switching',
            'maintenance_interval': 180
        },
        # Infrastructure
        {
            'name': 'HVAC Central Air Conditioning Unit',
            'category': 'infrastructure',
            'serial_no': 'HVAC-CAC-2020',
            'model': 'CAC-50TR',
            'manufacturer': 'Carrier',
            'department_name': 'Facilities',
            'responsible_name': 'Mukesh Thakur',
            'location': 'Building A - Rooftop',
            'maintenance_team_id': str(civil_team._id),
            'maintenance_team_name': civil_team.name,
            'technician_name': 'Ashok Kumar',
            'warranty_start': '2020-12-01',
            'warranty_duration': 24,
            'cost': 4500000.00,
            'purchase_date': '2020-11-25',
            'vendor': 'Carrier Airconditioning India',
            'state': 'active',
            'specifications': 'Capacity: 50 TR, Refrigerant: R410A, Compressor: Screw type',
            'maintenance_interval': 90
        }
    ]
    
    created_equipment = []
    for eq_data in equipment_data:
        equipment = Equipment.create(eq_data)
        created_equipment.append(equipment)
        print(f"  ✓ Created equipment: {equipment.name} ({equipment.serial_no})")
    
    print(f"✅ Created {len(created_equipment)} equipment items")
    return created_equipment

def seed_maintenance_requests(equipment_list, teams):
    """Create maintenance requests"""
    print("\n🔨 Creating Maintenance Requests...")
    
    today = datetime.now()
    
    # Various request scenarios
    requests_data = [
        # New Corrective Maintenance (Breakdown)
        {
            'equipment_id': str(equipment_list[0]._id),
            'maintenance_type': 'corrective',
            'priority': '3',
            'description': 'Hydraulic system pressure drop detected. Oil leakage from main cylinder seal. Immediate attention required.',
            'schedule_date': today.strftime('%Y-%m-%d'),
            'duration': 4.0,
            'state': 'new',
            'stage': 'new'
        },
        # In Progress Corrective
        {
            'equipment_id': str(equipment_list[2]._id),
            'maintenance_type': 'corrective',
            'priority': '2',
            'description': 'Forklift engine making unusual noise. Check engine timing and valve clearance.',
            'schedule_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'duration': 3.0,
            'state': 'in_progress',
            'stage': 'in_progress'
        },
        # Completed Corrective
        {
            'equipment_id': str(equipment_list[1]._id),
            'maintenance_type': 'corrective',
            'priority': '2',
            'description': 'CNC spindle alignment issue. Calibration required.',
            'schedule_date': (today - timedelta(days=5)).strftime('%Y-%m-%d'),
            'duration': 2.5,
            'actual_duration': 2.8,
            'state': 'done',
            'stage': 'repaired',
            'work_done': 'Spindle realigned, calibration completed, test run successful'
        },
        # Preventive Maintenance - Scheduled
        {
            'equipment_id': str(equipment_list[3]._id),
            'maintenance_type': 'preventive',
            'priority': '1',
            'description': 'Scheduled transformer oil testing and insulation resistance check',
            'schedule_date': (today + timedelta(days=7)).strftime('%Y-%m-%d'),
            'duration': 4.0,
            'state': 'new',
            'stage': 'new'
        },
        # Preventive Maintenance - Due Today
        {
            'equipment_id': str(equipment_list[4]._id),
            'maintenance_type': 'preventive',
            'priority': '1',
            'description': 'Quarterly DG maintenance: Oil change, filter replacement, battery check',
            'schedule_date': today.strftime('%Y-%m-%d'),
            'duration': 3.0,
            'state': 'new',
            'stage': 'new'
        },
        # Overdue Preventive
        {
            'equipment_id': str(equipment_list[5]._id),
            'maintenance_type': 'preventive',
            'priority': '2',
            'description': 'Server hardware health check and firmware update',
            'schedule_date': (today - timedelta(days=3)).strftime('%Y-%m-%d'),
            'duration': 2.0,
            'state': 'new',
            'stage': 'new',
            'is_overdue': True,
            'days_overdue': 3
        },
        # In Progress Preventive
        {
            'equipment_id': str(equipment_list[6]._id),
            'maintenance_type': 'preventive',
            'priority': '1',
            'description': 'Network switch configuration backup and port inspection',
            'schedule_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'duration': 1.5,
            'state': 'in_progress',
            'stage': 'in_progress'
        },
        # Completed Preventive
        {
            'equipment_id': str(equipment_list[7]._id),
            'maintenance_type': 'preventive',
            'priority': '1',
            'description': 'HVAC filter cleaning and refrigerant level check',
            'schedule_date': (today - timedelta(days=10)).strftime('%Y-%m-%d'),
            'duration': 3.0,
            'actual_duration': 3.2,
            'state': 'done',
            'stage': 'repaired',
            'work_done': 'Filters cleaned, refrigerant topped up, system tested'
        },
        # Future Preventive Maintenance
        {
            'equipment_id': str(equipment_list[0]._id),
            'maintenance_type': 'preventive',
            'priority': '1',
            'description': 'Monthly hydraulic system inspection and lubrication',
            'schedule_date': (today + timedelta(days=15)).strftime('%Y-%m-%d'),
            'duration': 2.0,
            'state': 'new',
            'stage': 'new'
        },
        {
            'equipment_id': str(equipment_list[1]._id),
            'maintenance_type': 'preventive',
            'priority': '1',
            'description': 'CNC machine quarterly calibration and accuracy check',
            'schedule_date': (today + timedelta(days=20)).strftime('%Y-%m-%d'),
            'duration': 4.0,
            'state': 'new',
            'stage': 'new'
        }
    ]
    
    created_requests = []
    for req_data in requests_data:
        request = MaintenanceRequest.create(req_data)
        created_requests.append(request)
        
        status_icon = {
            'new': '🆕',
            'in_progress': '⚙️',
            'done': '✅',
            'cancelled': '❌'
        }
        
        print(f"  {status_icon.get(request.state, '📋')} Created request: {request.name} - {request.equipment_name}")
    
    print(f"✅ Created {len(created_requests)} maintenance requests")
    return created_requests

def main():
    """Main seeder function"""
    print("=" * 70)
    print("🌱 DATA SEEDER - Maintenance Management System")
    print("=" * 70)
    print("\n⚠️  This will create REAL data in the database")
    print("   NO MOCK DATA - All records are created via ORM\n")
    
    # Initialize database
    print("🔌 Initializing database connection...")
    init_db()
    print("✅ Database connected\n")
    
    # Seed data
    teams = seed_maintenance_teams()
    equipment = seed_equipment(teams)
    requests = seed_maintenance_requests(equipment, teams)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ DATA SEEDING COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"   • Maintenance Teams: {len(teams)}")
    print(f"   • Equipment Items: {len(equipment)}")
    print(f"   • Maintenance Requests: {len(requests)}")
    print(f"\n🎉 System is ready for demo!\n")
    print("=" * 70)

if __name__ == '__main__':
    main()
