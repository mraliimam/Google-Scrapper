from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scrapper.db'
app.config['SECRET_KEY'] = 'ec9439cfc6c796ae2029594d'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['USE_ROLE_PERMISSIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"

bcrypt = Bcrypt(app)

from market import models

from market import routes