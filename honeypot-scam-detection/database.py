"""
Database module for storing scam intelligence
Handles all SQLite database operations
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
import os

DATABASE_FILE = 'scam_intelligence.db'

def init_database():
    """Initialize the database and create tables if they don't exist"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create scam sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            scam_detected BOOLEAN NOT NULL,
            scam_confidence REAL,
            scam_type TEXT,
            messages_exchanged INTEGER NOT NULL,
            bank_accounts TEXT,
            upi_ids TEXT,
            phishing_links TEXT,
            phone_numbers TEXT,
            suspicious_keywords TEXT,
            agent_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            guvi_callback_sent BOOLEAN DEFAULT 0,
            guvi_callback_status INTEGER
        )
    ''')
    
    # Create conversation messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            message_text TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            FOREIGN KEY (session_id) REFERENCES scam_sessions (session_id)
        )
    ''')
    
    # Create statistics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE DEFAULT CURRENT_DATE,
            total_sessions INTEGER DEFAULT 0,
            scams_detected INTEGER DEFAULT 0,
            total_messages INTEGER DEFAULT 0,
            intelligence_extracted INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")

def save_session(session_data):
    """Save or update a session in the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        intel = session_data.intelligence
        
        cursor.execute('''
            INSERT OR REPLACE INTO scam_sessions 
            (session_id, scam_detected, scam_confidence, scam_type,
             messages_exchanged, bank_accounts, upi_ids, phishing_links,
             phone_numbers, suspicious_keywords, agent_notes, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_data.session_id,
            session_data.scam_detected,
            session_data.scam_confidence,
            getattr(session_data, 'scam_type', ''),
            session_data.messages_exchanged,
            json.dumps(intel.bank_accounts),
            json.dumps(intel.upi_ids),
            json.dumps(intel.phishing_links),
            json.dumps(intel.phone_numbers),
            json.dumps(intel.suspicious_keywords),
            session_data.agent_notes,
            datetime.now() if session_data.conversation_complete else None
        ))
        
        conn.commit()
        print(f"💾 Session {session_data.session_id} saved to database")
        return True
        
    except Exception as e:
        print(f"Error saving session: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def save_message(session_id: str, sender: str, message_text: str, timestamp: str):
    """Save a conversation message to the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO conversation_messages (session_id, sender, message_text, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (session_id, sender, message_text, timestamp))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error saving message: {e}")
        return False
    finally:
        conn.close()

def update_guvi_callback_status(session_id: str, status_code: int):
    """Update the GUVI callback status for a session"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE scam_sessions 
            SET guvi_callback_sent = 1, guvi_callback_status = ?
            WHERE session_id = ?
        ''', (status_code, session_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error updating callback status: {e}")
        return False
    finally:
        conn.close()

def get_session(session_id: str) -> Optional[Dict]:
    """Retrieve a session from the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM scam_sessions WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
        
    finally:
        conn.close()

def get_all_sessions(limit: int = 100) -> List[Dict]:
    """Retrieve all sessions from the database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM scam_sessions 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        return [dict(zip(columns, row)) for row in rows]
        
    finally:
        conn.close()

def get_conversation_history(session_id: str) -> List[Dict]:
    """Retrieve all messages for a session"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT sender, message_text, timestamp 
            FROM conversation_messages 
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))
        
        rows = cursor.fetchall()
        
        return [
            {
                "sender": row[0],
                "text": row[1],
                "timestamp": row[2]
            }
            for row in rows
        ]
        
    finally:
        conn.close()

def get_statistics() -> Dict:
    """Get overall statistics"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        # Total sessions
        cursor.execute('SELECT COUNT(*) FROM scam_sessions')
        total_sessions = cursor.fetchone()[0]
        
        # Scams detected
        cursor.execute('SELECT COUNT(*) FROM scam_sessions WHERE scam_detected = 1')
        scams_detected = cursor.fetchone()[0]
        
        # Total messages
        cursor.execute('SELECT SUM(messages_exchanged) FROM scam_sessions')
        total_messages = cursor.fetchone()[0] or 0
        
        # Intelligence extracted (sessions with at least one piece of intel)
        cursor.execute('''
            SELECT COUNT(*) FROM scam_sessions 
            WHERE bank_accounts != '[]' 
               OR upi_ids != '[]' 
               OR phishing_links != '[]' 
               OR phone_numbers != '[]'
        ''')
        intelligence_extracted = cursor.fetchone()[0]
        
        # Average confidence
        cursor.execute('SELECT AVG(scam_confidence) FROM scam_sessions WHERE scam_detected = 1')
        avg_confidence = cursor.fetchone()[0] or 0
        
        return {
            "total_sessions": total_sessions,
            "scams_detected": scams_detected,
            "total_messages": total_messages,
            "intelligence_extracted": intelligence_extracted,
            "average_confidence": avg_confidence,
            "detection_rate": (scams_detected / total_sessions * 100) if total_sessions > 0 else 0
        }
        
    finally:
        conn.close()

def export_to_csv(filename: str = 'scam_export.csv') -> bool:
    """Export all sessions to CSV file"""
    import csv
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM scam_sessions ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        if not rows:
            print("No data to export")
            return False
        
        columns = [description[0] for description in cursor.description]
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
        
        print(f"✓ Exported {len(rows)} sessions to {filename}")
        return True
        
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False
    finally:
        conn.close()

def cleanup_old_sessions(days: int = 30) -> int:
    """Delete sessions older than specified days"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM scam_sessions 
            WHERE created_at < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        deleted = cursor.rowcount
        conn.commit()
        
        print(f"✓ Deleted {deleted} old sessions")
        return deleted
        
    except Exception as e:
        print(f"Error cleaning up sessions: {e}")
        return 0
    finally:
        conn.close()

def get_top_scammers(limit: int = 10) -> List[Dict]:
    """Get sessions with most intelligence extracted"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                session_id,
                scam_confidence,
                messages_exchanged,
                bank_accounts,
                upi_ids,
                phishing_links,
                phone_numbers,
                created_at
            FROM scam_sessions 
            WHERE scam_detected = 1
            ORDER BY messages_exchanged DESC, scam_confidence DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        return [dict(zip(columns, row)) for row in rows]
        
    finally:
        conn.close()

if __name__ == '__main__':
    # Test database initialization
    init_database()
    print("Database module loaded successfully!")
