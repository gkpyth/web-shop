import stripe
from flask import Flask
from dotenv import load_dotenv
from extensions import db, login_manager, bcrypt
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

db.init_app(app)
login_manager.init_app(app)
bcrypt.init_app(app)
login_manager.login_view = 'login'

from models import *

with app.app_context():
    db.create_all()

from routes import *

if __name__ == '__main__':
    app.run(debug=os.getenv("DEBUG") == "1")