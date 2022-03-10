from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content')
    is_private = BooleanField('Private')
    submit = SubmitField('Publish')
