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
    
    flask_env = os.environ.get('FLASK_ENV', 'development').lower()
    secret_key = os.environ.get('SECRET_KEY')

    if not secret_key:
        if flask_env == 'production':
            raise RuntimeError('SECRET_KEY must be set in production.')
        secret_key = 'dev-only-insecure-key-change-before-production'

    if flask_env == 'production' and secret_key in {
        'dev-key-123',
        'dev_secret_key_change_me',
        'dev-only-insecure-key-change-before-production',
    }:
        raise RuntimeError('Weak SECRET_KEY is not allowed in production.')

    app.config['SECRET_KEY'] = secret_key
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')
    
    # Connection initialization is handled lazily by the Database helper.
    
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
