from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, PasswordField
from wtforms.validators import DataRequired


class BusinessForm(FlaskForm):
    BusinessName = StringField(label = 'Business Name', validators=[DataRequired()])
    url = StringField(label = 'Profile URL', validators=[DataRequired()])
    ReviewsCount = IntegerField()
    Review = IntegerField()
    submit = SubmitField(label='Submit')

class LoginForm(FlaskForm):
    username = StringField(label = 'User Name: ', validators=[DataRequired()])
    password = PasswordField(label = 'Password:',validators=[DataRequired()])
    submit = SubmitField(label='Login')