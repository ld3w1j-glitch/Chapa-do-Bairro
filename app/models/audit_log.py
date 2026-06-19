from datetime import datetime
from app.extensions import db

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, default="admin")
    action = db.Column(db.String(120), nullable=False)
    entity = db.Column(db.String(80), nullable=True)
    entity_id = db.Column(db.String(40), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def created_br(self):
        return self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else '-'
