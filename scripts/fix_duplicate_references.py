"""
Fix Duplicate Reference Numbers Script
Run this once to fix existing duplicate 'name' fields in maintenance_request collection
"""
from pymongo import MongoClient
from datetime import datetime
import random
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://keval:UkqdDpDf1QJsyMoh@cluster0.aivlzx3.mongodb.net/?appName=Cluster0')
client = MongoClient(MONGO_URI)
db = client['maintenance_management']
collection = db['maintenance_request']

print("=" * 60)
print("FIXING DUPLICATE REFERENCE NUMBERS")
print("=" * 60)

# Find all documents grouped by name
pipeline = [
    {
        '$group': {
            '_id': '$name',
            'count': {'$sum': 1},
            'ids': {'$push': '$_id'}
        }
    },
    {
        '$match': {
            'count': {'$gt': 1}
        }
    }
]

duplicates = list(collection.aggregate(pipeline))

if not duplicates:
    print("✓ No duplicate reference numbers found!")
    print("Database is clean.")
else:
    print(f"Found {len(duplicates)} duplicate reference numbers")
    print()
    
    total_fixed = 0
    for dup in duplicates:
        original_name = dup['_id']
        ids = dup['ids']
        count = dup['count']
        
        print(f"Fixing: {original_name} ({count} duplicates)")
        
        # Keep first record with original name, update the rest
        for i, doc_id in enumerate(ids[1:], start=1):
            # Generate unique reference
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = random.randint(1000, 9999)
            new_name = f"MNT-{timestamp}-{random_suffix}"
            
            # Update document
            result = collection.update_one(
                {'_id': doc_id},
                {
                    '$set': {
                        'name': new_name,
                        'write_date': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"  ✓ Updated {doc_id} → {new_name}")
                total_fixed += 1
            else:
                print(f"  ✗ Failed to update {doc_id}")
        
        print()
    
    print("=" * 60)
    print(f"SUMMARY: Fixed {total_fixed} duplicate records")
    print("=" * 60)

# Verify no duplicates remain
remaining = list(collection.aggregate(pipeline))
if remaining:
    print(f"⚠ WARNING: {len(remaining)} duplicates still exist!")
else:
    print("✓ SUCCESS: All duplicates resolved!")

client.close()
