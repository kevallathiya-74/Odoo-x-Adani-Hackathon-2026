# 🚀 QUICK START GUIDE - GearGuard Maintenance Management System

## ⚡ 5-Minute Setup

### Step 1: Verify MongoDB is Running
```bash
# Check if MongoDB is running (Windows)
Get-Process mongod

# If not running, start MongoDB service
net start MongoDB
```

### Step 2: Install Dependencies
```bash
cd D:\Odoo-x-Adani-Hackathon-2026
pip install -r requirements.txt
```

### Step 3: Seed Data
```bash
python seed_data.py
```

### Step 4: Run Tests (Optional but Recommended)
```bash
python test_system.py
```

### Step 5: Start Application
```bash
python app.py
```

### Step 6: Access System
Open browser: **http://localhost:5000**

---

## 📋 System Tour

### 1. Dashboard
- Real-time statistics
- Equipment status overview
- Maintenance request tracking
- Interactive charts

### 2. Equipment Management
**URL**: http://localhost:5000/equipment

**Features**:
- Create new equipment
- Track warranty
- Assign maintenance teams
- View maintenance history
- Scrap/Reactivate equipment

### 3. Maintenance Kanban
**URL**: http://localhost:5000/maintenance/kanban

**Features**:
- Drag & drop between stages
- Visual priority indicators
- Overdue alerts (red border)
- Technician avatars
- Real-time updates

**Stages**:
- 🆕 New: Newly created requests
- ⚙️ In Progress: Active maintenance
- ✅ Repaired: Completed successfully
- 🗑️ Scrap: Equipment marked for disposal

### 4. Calendar View
**URL**: http://localhost:5000/maintenance/calendar

**Features**:
- Preventive maintenance scheduling
- Monthly/Weekly/Daily views
- Click to create new schedule
- Visual priority coding

### 5. Reports & Analytics
**URL**: http://localhost:5000/reports

**Features**:
- Pivot table analysis
- Interactive charts
- Equipment utilization
- Team performance

---

## 🎯 Key Workflows

### Creating Equipment
1. Navigate to Equipment → New Equipment
2. Fill basic information (Name, Category, Location)
3. Assign maintenance team and technician
4. Set warranty details
5. Save

**Auto-generated**: Serial number, equipment code

### Creating Maintenance Request
1. Go to Maintenance → New Request
2. Select equipment (auto-fills team, technician, location)
3. Choose type: Corrective or Preventive
4. Set priority and schedule date
5. Save

**Auto-generated**: Reference number (MNT-YYYYMMDDHHMMSS)

### Kanban Workflow
1. **New Request**: Created by user
2. **Drag to "In Progress"**: 
   - Sets start_date automatically
   - Equipment status → "Under Maintenance"
3. **Drag to "Repaired"**:
   - Sets end_date automatically
   - Calculates actual duration
   - Equipment status → "Active"
4. **Drag to "Scrap"**:
   - Equipment marked as scrapped
   - All pending requests cancelled

### Handling Overdue Requests
- System auto-detects overdue based on schedule_date
- Red border on Kanban cards
- Overdue badge displayed
- Dashboard shows count

---

## 🔍 Testing Data

After running `seed_data.py`, you'll have:

**4 Maintenance Teams**:
- Mechanical Maintenance Team
- Electrical Maintenance Team
- IT & Software Team
- Civil Infrastructure Team

**8 Equipment Items**:
- Hydraulic Press Machine
- CNC Milling Machine
- Forklift Truck
- Transformer
- Diesel Generator
- Server
- Network Switch
- HVAC Unit

**10 Maintenance Requests**:
- Mix of Corrective & Preventive
- Various states (New, In Progress, Done)
- Some overdue for testing

---

## 🐛 Troubleshooting

### MongoDB Connection Failed
```bash
# Check MongoDB is running
Get-Service MongoDB

# Start MongoDB
net start MongoDB

# Or use MongoDB Compass to start local instance
```

### Port 5000 Already in Use
Edit `config.py`:
```python
PORT = 5001  # Change port
```

### Dependencies Not Installing
```bash
# Use virtual environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Data Not Showing
```bash
# Re-run seeder
python seed_data.py

# Check database
python -c "from core import init_db; init_db(); print('DB OK')"
```

---

## 📊 API Endpoints

### Equipment
- `GET /api/equipment` - List all equipment
- `POST /api/equipment` - Create equipment
- `GET /api/equipment/<id>` - Get single equipment
- `PUT /api/equipment/<id>` - Update equipment
- `DELETE /api/equipment/<id>` - Delete equipment
- `POST /api/equipment/<id>/scrap` - Scrap equipment

### Maintenance Requests
- `GET /api/maintenance` - List all requests
- `POST /api/maintenance` - Create request
- `GET /api/maintenance/<id>` - Get single request
- `PUT /api/maintenance/<id>` - Update request
- `POST /api/maintenance/<id>/start` - Start maintenance
- `POST /api/maintenance/<id>/done` - Complete maintenance
- `GET /api/maintenance/kanban` - Kanban data
- `GET /api/maintenance/calendar` - Calendar events

### Teams
- `GET /api/teams` - List all teams
- `POST /api/teams` - Create team

### Reports
- `GET /api/reports/pivot` - Pivot data
- `GET /api/reports/charts` - Chart data

---

## 🎨 Customization

### Adding New Fields
1. Edit model in `addons/maintenance_management/models/`
2. Add field definition using `fields.Char()`, `fields.Integer()`, etc.
3. Update form template in `templates/`
4. Restart application

### Changing Colors
Edit `static/css/odoo-style.css`:
```css
:root {
    --odoo-primary: #714B67;  /* Change this */
}
```

---

## 💡 Pro Tips

1. **Keyboard Shortcuts**:
   - `Ctrl+N` in list views → New record
   - `Ctrl+S` in forms → Save
   - `Esc` → Cancel/Close

2. **Quick Filters**:
   - Use dropdown filters in list views
   - Search box for instant filtering

3. **Bulk Operations**:
   - Select multiple records (future feature)
   - Apply actions to all

4. **Export Data**:
   - Use `/api/reports/pivot` for data export
   - JSON format, easy to process

---

## 🚀 Production Deployment

### MongoDB Atlas (Cloud)
1. Create free cluster at mongodb.com/cloud/atlas
2. Get connection string
3. Update `config.py`:
```python
MONGO_URI = 'mongodb+srv://user:pass@cluster.mongodb.net/'
```

### Environment Variables
```bash
# .env file
MONGO_URI=mongodb+srv://...
SECRET_KEY=your-secret-key
DEBUG=False
```

### Run with Gunicorn (Linux/Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📞 Support

For issues during hackathon:
- Check MongoDB connection
- Review `app.log` for errors
- Run `test_system.py` to diagnose
- Check firewall/antivirus settings

**Good luck with the hackathon! 🏆**
