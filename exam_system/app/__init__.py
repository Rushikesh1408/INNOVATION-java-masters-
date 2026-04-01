from flask import Flask, redirect, url_for
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os
from .db import Database

bcrypt = Bcrypt()

def create_app():
    load_dotenv()
    
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')
    
    # Database.initialize() is not needed for SQLite
    
    # Initialize Bcrypt
    bcrypt.init_app(app)
    
    # Register Blueprints
    from .routes.admin import admin_bp
    from .routes.contestant import contestant_bp
    
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(contestant_bp, url_prefix='/contestant')
    
    @app.route('/')
    def root():
        return redirect(url_for('contestant.home'))
    
    return app
