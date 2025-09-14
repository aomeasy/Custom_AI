from app import db
from datetime import datetime

class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.String(80))
    
    @staticmethod
    def get_setting(key, default=None):
        setting = AppSettings.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @staticmethod
    def set_setting(key, value, description=None, updated_by=None):
        setting = AppSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
            if updated_by:
                setting.updated_by = updated_by
        else:
            setting = AppSettings(
                key=key, 
                value=value, 
                description=description, 
                updated_by=updated_by
            )
            db.session.add(setting)
        db.session.commit()
        return setting
