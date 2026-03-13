"""
Database initialization utilities
"""
from app.db.database import engine, Base
from app.db.models import AuditRecordDB, SecretAuditRecordDB


def initialize_database():
    """Initialize database and create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized - audit_records and secret_audit_records tables ready")


def clear_old_records(days: int = 90):
    """Delete audit records older than specified days (maintenance task)"""
    from sqlalchemy import delete
    from datetime import datetime, timedelta
    from app.db.database import SessionLocal
    
    db = SessionLocal()
    try:
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        deleted = db.execute(
            delete(AuditRecordDB).where(AuditRecordDB.timestamp < cutoff_date)
        )
        db.commit()
        print(f"🗑️  Deleted {deleted.rowcount} audit records older than {days} days")
        return deleted.rowcount
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing old records: {str(e)}")
        return 0
    finally:
        db.close()
