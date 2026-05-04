from urllib.parse import urlsplit

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import app
from extensions import db
from models import User
from forms import RegisterForm, LoginForm


@ app.route('/')
def home():
    return render_template('home.html')


@ app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        # SECURITY: check duplicate email before creating user
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        user = User()
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@ app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # SECURITY: same error message whether email or password is wrong
        # Never tell the potential attacker which one failed
        if not user or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        # SECURITY: redirect to intended page after login
        next_page = request.args.get('next')
        return redirect(next_page or url_for('home'))
    return render_template('login.html', form=form)


@ app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))