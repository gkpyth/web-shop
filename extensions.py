from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import stripe
import os

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()