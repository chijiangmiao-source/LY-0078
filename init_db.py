# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlobject import connectionForURI, sqlhub

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'breakfast_management.db')
db_path = db_path.replace('\\', '/')
db_uri = f'sqlite:///{db_path}'

print(f"Initializing database: {db_uri}")

conn = connectionForURI(db_uri)
sqlhub.processConnection = conn

from breakfast_management import model
model.init_model(sqlhub)

print("Database initialization complete!")

try:
    from breakfast_management.model import WasteRecord
    count = WasteRecord.select().count()
    print(f"WasteRecord table exists, current records: {count}")
except Exception as e:
    print(f"WasteRecord table check failed: {e}")
