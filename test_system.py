"""
Comprehensive Test Suite for Maintenance Management System
Tests all CRUD operations and business logic
"""
import sys
from datetime import datetime, timedelta
from core import init_db
from addons.maintenance_management.models import Equipment, MaintenanceTeam, MaintenanceRequest

def test_database_connection():
    """Test MongoDB connection"""
    print("\n🔌 Testing Database Connection...")
    try:
        db = init_db()
        print("   ✅ Database connected successfully")
        return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def test_maintenance_team_crud():
    """Test MaintenanceTeam CRUD operations"""
    print("\n👥 Testing Maintenance Team CRUD...")
    
    # CREATE
    print("   📝 Testing CREATE...")
    team_data = {
        'name': 'Test Team',
        'specialization': 'mechanical',
        'team_leader_name': 'Test Leader',
        'email': 'test@example.com',
        'active': True
    }
    team = MaintenanceTeam.create(team_data)
    assert team.name == 'Test Team', "Create failed"
    assert team.code is not None, "Auto-generated code missing"
    print(f"   ✅ CREATE: Team created with ID {team._id}")
    
    # READ
    print("   📖 Testing READ...")
    teams = MaintenanceTeam.search([('name', '=', 'Test Team')])
    assert len(teams) > 0, "Search failed"
    assert teams[0].name == 'Test Team', "Read failed"
    print(f"   ✅ READ: Found {len(teams)} team(s)")
    
    # UPDATE
    print("   ✏️  Testing UPDATE...")
    team.write({'email': 'updated@example.com'})
    updated_teams = MaintenanceTeam.browse([str(team._id)])
    assert updated_teams[0].email == 'updated@example.com', "Update failed"
    print("   ✅ UPDATE: Email updated successfully")
    
    # DELETE
    print("   🗑️  Testing DELETE...")
    team.unlink()
    deleted_teams = MaintenanceTeam.browse([str(team._id)])
    assert len(deleted_teams) == 0, "Delete failed"
    print("   ✅ DELETE: Team deleted successfully")
    
    return True

def test_equipment_crud():
    """Test Equipment CRUD operations"""
    print("\n🔧 Testing Equipment CRUD...")
    
    # CREATE with auto-fill logic
    print("   📝 Testing CREATE with business logic...")
    equipment_data = {
        'name': 'Test Machine',
        'category': 'machine',
        'location': 'Test Location',
        'maintenance_team_name': 'Test Team',
        'warranty_start': '2024-01-01',
        'warranty_duration': 12,
        'state': 'active'
    }
    equipment = Equipment.create(equipment_data)
    assert equipment.name == 'Test Machine', "Create failed"
    assert equipment.serial_no is not None, "Serial number not auto-generated"
    assert equipment.warranty_end is not None, "Warranty end date not calculated"
    print(f"   ✅ CREATE: Equipment created with serial {equipment.serial_no}")
    
    # Test state transitions
    print("   🔄 Testing state transitions...")
    equipment.write({'state': 'under_maintenance'})
    assert equipment.state == 'under_maintenance', "State change failed"
    print("   ✅ State changed to 'under_maintenance'")
    
    # Test scrap action
    print("   🗑️  Testing SCRAP action...")
    equipment.action_scrap()
    assert equipment.state == 'scrapped', "Scrap action failed"
    print("   ✅ Equipment scrapped successfully")
    
    # Cleanup
    equipment.unlink()
    return True

def test_maintenance_request_workflow():
    """Test MaintenanceRequest complete workflow"""
    print("\n🔨 Testing Maintenance Request Workflow...")
    
    # Create dependencies
    print("   📋 Creating test dependencies...")
    team = MaintenanceTeam.create({
        'name': 'Test Workflow Team',
        'specialization': 'mechanical',
        'active': True
    })
    
    equipment = Equipment.create({
        'name': 'Test Equipment for Workflow',
        'category': 'machine',
        'location': 'Test Location',
        'maintenance_team_id': str(team._id),
        'maintenance_team_name': team.name,
        'technician_name': 'Test Technician',
        'state': 'active'
    })
    
    # CREATE request with auto-fill
    print("   📝 Testing CREATE with auto-fill...")
    request_data = {
        'equipment_id': str(equipment._id),
        'maintenance_type': 'corrective',
        'priority': '2',
        'description': 'Test maintenance request',
        'schedule_date': datetime.now().strftime('%Y-%m-%d'),
        'duration': 2.0
    }
    request = MaintenanceRequest.create(request_data)
    assert request.name is not None, "Reference not auto-generated"
    assert request.equipment_name == equipment.name, "Equipment name not auto-filled"
    assert request.team_id == str(team._id), "Team not auto-filled"
    print(f"   ✅ CREATE: Request {request.name} created with auto-fill")
    
    # Test workflow: New → In Progress
    print("   ▶️  Testing workflow: New → In Progress...")
    request.action_start()
    assert request.state == 'in_progress', "Start action failed"
    assert request.start_date is not None, "Start date not set"
    
    # Check equipment status changed
    updated_equipment = Equipment.browse([str(equipment._id)])[0]
    assert updated_equipment.state == 'under_maintenance', "Equipment status not updated"
    print("   ✅ Status: New → In Progress (Equipment status updated)")
    
    # Test workflow: In Progress → Done
    print("   ✅ Testing workflow: In Progress → Done...")
    request.action_done()
    assert request.state == 'done', "Done action failed"
    assert request.end_date is not None, "End date not set"
    assert request.actual_duration is not None, "Actual duration not calculated"
    
    # Check equipment status reverted
    updated_equipment = Equipment.browse([str(equipment._id)])[0]
    assert updated_equipment.state == 'active', "Equipment status not reverted"
    print("   ✅ Status: In Progress → Done (Equipment reactivated)")
    
    # Test overdue detection
    print("   ⏰ Testing overdue detection...")
    overdue_request = MaintenanceRequest.create({
        'equipment_id': str(equipment._id),
        'maintenance_type': 'preventive',
        'priority': '1',
        'description': 'Overdue test',
        'schedule_date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        'duration': 1.0
    })
    assert overdue_request.is_overdue == True, "Overdue not detected"
    print("   ✅ Overdue detection working")
    
    # Cleanup
    print("   🧹 Cleaning up test data...")
    request.unlink()
    overdue_request.unlink()
    equipment.unlink()
    team.unlink()
    print("   ✅ Cleanup completed")
    
    return True

def test_search_operations():
    """Test advanced search operations"""
    print("\n🔍 Testing Search Operations...")
    
    # Create test data
    team = MaintenanceTeam.create({
        'name': 'Search Test Team',
        'specialization': 'electrical',
        'active': True
    })
    
    # Test domain search
    print("   📊 Testing domain search...")
    teams = MaintenanceTeam.search([
        ('specialization', '=', 'electrical'),
        ('active', '=', True)
    ])
    assert len(teams) > 0, "Domain search failed"
    print(f"   ✅ Found {len(teams)} team(s) with domain search")
    
    # Test search_count
    print("   🔢 Testing search_count...")
    count = MaintenanceTeam.search_count([('active', '=', True)])
    assert count > 0, "Search count failed"
    print(f"   ✅ Count: {count} active teams")
    
    # Test ordering
    print("   📑 Testing ordering...")
    teams = MaintenanceTeam.search([], order='name ASC', limit=5)
    assert len(teams) <= 5, "Limit not applied"
    print(f"   ✅ Retrieved {len(teams)} teams with ordering")
    
    # Cleanup
    team.unlink()
    return True

def test_data_integrity():
    """Test data integrity and relationships"""
    print("\n🔐 Testing Data Integrity...")
    
    # Create chain of related records
    team = MaintenanceTeam.create({
        'name': 'Integrity Test Team',
        'specialization': 'it',
        'active': True
    })
    
    equipment = Equipment.create({
        'name': 'Integrity Test Equipment',
        'category': 'it_asset',
        'location': 'Test',
        'maintenance_team_id': str(team._id),
        'maintenance_team_name': team.name,
        'state': 'active'
    })
    
    request = MaintenanceRequest.create({
        'equipment_id': str(equipment._id),
        'maintenance_type': 'preventive',
        'priority': '1',
        'description': 'Integrity test',
        'schedule_date': datetime.now().strftime('%Y-%m-%d'),
        'duration': 1.0
    })
    
    # Verify relationships
    assert request.equipment_id == str(equipment._id), "Equipment relationship broken"
    assert request.team_id == str(team._id), "Team relationship broken"
    print("   ✅ Relationships maintained correctly")
    
    # Test cascade behavior
    print("   🔗 Testing scrap cascade...")
    equipment.action_scrap()
    
    # Request should be cancelled
    updated_request = MaintenanceRequest.browse([str(request._id)])[0]
    assert updated_request.state == 'cancelled', "Cascade cancellation failed"
    print("   ✅ Scrap action cascaded to requests")
    
    # Cleanup
    request.unlink()
    equipment.unlink()
    team.unlink()
    
    return True

def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("🧪 MAINTENANCE MANAGEMENT SYSTEM - TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Maintenance Team CRUD", test_maintenance_team_crud),
        ("Equipment CRUD", test_equipment_crud),
        ("Maintenance Request Workflow", test_maintenance_request_workflow),
        ("Search Operations", test_search_operations),
        ("Data Integrity", test_data_integrity)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"\n   ❌ Test FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review errors above.")
    
    print("=" * 70)
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
