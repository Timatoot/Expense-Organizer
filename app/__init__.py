from flask import Flask
from .auth.routes import auth_blueprint
from .expense.routes import expense_blueprint
from flask_login import LoginManager
from .models import User
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(expense_blueprint)

    return app
