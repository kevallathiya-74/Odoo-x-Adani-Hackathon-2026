"""
MongoDB Setup and Installation Guide

OPTION 1: Use MongoDB Atlas (Cloud - Recommended for Demo)
=========================================================
1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free account
3. Create a free cluster (M0)
4. Get connection string
5. Update config.py:
   MONGO_URI = 'mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority'

OPTION 2: Install MongoDB Locally
===================================
Windows:
1. Download from https://www.mongodb.com/try/download/community
2. Run installer
3. Select "Complete" installation
4. Install as Windows Service
5. Verify: Open Command Prompt and type `mongod --version`

Linux:
```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

MacOS:
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

OPTION 3: Use MongoDB in Docker
================================
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

OPTION 4: Mock Database (For Testing Only)
===========================================
If you don't have MongoDB installed, the system will use an in-memory
database for testing purposes. This is NOT suitable for production.

To enable mock mode, set in config.py:
USE_MOCK_DB = True

Verification:
=============
After installation, run:
```bash
python test_system.py
```

This will verify your database connection and test all functionality.
"""

print(__doc__)
