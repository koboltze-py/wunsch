#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Datenbank-Migration für Version 2.5
Fügt folgende Änderungen hinzu:
- updated_at Spalte zu shift_requests
- shift_notes Tabelle
"""

import os
import sys
from app import app, db
from sqlalchemy import text, inspect

def check_column_exists(table_name, column_name):
    """Prüft ob eine Spalte existiert"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def check_table_exists(table_name):
    """Prüft ob eine Tabelle existiert"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def migrate():
    """Führt die Migration durch"""
    with app.app_context():
        print("🔄 Starte Datenbank-Migration...")
        
        # Prüfe ob updated_at Spalte existiert
        if not check_column_exists('shift_requests', 'updated_at'):
            print("   Füge updated_at Spalte zu shift_requests hinzu...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE shift_requests 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                conn.commit()
            print("   ✓ updated_at Spalte hinzugefügt")
        else:
            print("   ✓ updated_at Spalte existiert bereits")
        
        # Prüfe ob shift_notes Tabelle existiert
        if not check_table_exists('shift_notes'):
            print("   Erstelle shift_notes Tabelle...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE shift_notes (
                        id SERIAL PRIMARY KEY,
                        shift_request_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (shift_request_id) REFERENCES shift_requests(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                conn.commit()
            print("   ✓ shift_notes Tabelle erstellt")
        else:
            print("   ✓ shift_notes Tabelle existiert bereits")
        
        print("✅ Migration erfolgreich abgeschlossen!")

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {e}")
        sys.exit(1)
