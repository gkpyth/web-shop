from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, URL, Optional


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    image_url = StringField('Image URL', validators=[Optional(), URL()])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=[
        ('coffee', 'Coffee'),
        ('drinkware', 'Drinkware'),
        ('gear', 'Gear'),
        ('lifestyle', 'Lifestyle')
    ])
    subcategory = SelectField('Subcategory', choices=[
        ('whole-bean', 'Whole Bean'),
        ('ground', 'Ground'),
        ('cold-brew', 'Cold Brew'),
        ('mugs', 'Mugs'),
        ('tumblers', 'Tumblers & Thermoses'),
        ('brewing', 'Brewing'),
        ('grinding', 'Grinding'),
        ('apparel', 'Apparel'),
        ('accessories', 'Accessories'),
        ('home', 'Home')
    ])
    submit = SubmitField('Save Product')
