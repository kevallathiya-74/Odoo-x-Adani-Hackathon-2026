# GearGuard Maintenance Management System - Startup Script

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "🚀 GEARGUARD - MAINTENANCE MANAGEMENT SYSTEM" -ForegroundColor Green
Write-Host "   Odoo × Adani Hackathon 2026" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "🐍 Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python not found! Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check MongoDB
Write-Host "🍃 Checking MongoDB connection..." -ForegroundColor Cyan
Write-Host "   ℹ️  Make sure MongoDB is running on localhost:27017" -ForegroundColor Yellow
Write-Host "   ℹ️  Or update MONGO_URI in config.py for cloud MongoDB" -ForegroundColor Yellow

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Cyan
try {
    & pip install -r requirements.txt --quiet
    Write-Host "   ✅ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Ask about seeding data
Write-Host "`n🌱 Do you want to seed initial data?" -ForegroundColor Cyan
Write-Host "   This will create:" -ForegroundColor White
Write-Host "   • 4 Maintenance Teams" -ForegroundColor White
Write-Host "   • 8 Equipment Items" -ForegroundColor White
Write-Host "   • 10 Maintenance Requests" -ForegroundColor White
Write-Host ""
$seedChoice = Read-Host "   Seed data? (Y/N)"

if ($seedChoice -eq "Y" -or $seedChoice -eq "y") {
    Write-Host "`n   Running data seeder..." -ForegroundColor Cyan
    try {
        & python seed_data.py
        Write-Host "   ✅ Data seeded successfully" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Seeding failed, but continuing..." -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⏭️  Skipping data seeding" -ForegroundColor Yellow
}

# Start the application
Write-Host "`n🎯 Starting Flask application..." -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""
Write-Host "   📡 Server will start on: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000" -ForegroundColor Green
Write-Host "   🌐 Access the system: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000" -ForegroundColor Green
Write-Host ""
Write-Host "   Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Run the Flask app
try {
    & python app.py
} catch {
    Write-Host "`n❌ Application failed to start!" -ForegroundColor Red
    Write-Host "   Check if MongoDB is running" -ForegroundColor Yellow
    Write-Host "   Check if port 5000 is available" -ForegroundColor Yellow
    exit 1
}
