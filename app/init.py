from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'กรุณาเข้าสู่ระบบเพื่อใช้งาน'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.chat import chat_bp
    from app.routes.settings import settings_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        db.create_all()
        # Initialize default admin user
        from app.models.user import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))
