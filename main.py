from flask import Flask, render_template, url_for, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.users import User
from data.news import News
from data.register import RegisterForm
from data.login import LoginForm
from data.news_form import NewsForm
import os

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'some_randomly_generated_string'

db_session.global_init('db/blogs.sqlite')


@app.route('/')
def index_page():
    session = db_session.create_session()
    if current_user.is_authenticated:
        news = session.query(News).filter(
            (News.user == current_user) | (News.is_private != True)).all()
    else:
        news = session.query(News).filter(News.is_private != True).all()
    return render_template('index.html', newsdata=news)


@app.route('/reg', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            return render_template('reg.html', form=form, pas_err='Passwords do not match')
        session = db_session.create_session()
        if session.query(User).filter(User.login == form.username.data).first():
            return render_template('reg.html', form=form, user_err='User already exists')
        user = User(login=form.username.data)
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect(url_for('login_page'))
    return render_template('reg.html', form=form)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.login == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', message='Incorrect login or password', form=form)
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect('/')


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        # merge used when you have several objects which map to the same database record.
        # Copies the state of a given instance into a corresponding instance within this Session
        session.merge(current_user)
        session.commit()
        return redirect('/')
    return render_template('news.html', form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html', form=form)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_news(id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == id, News.user == current_user).first()
    if news:
        session.delete(news)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(401)
def authorization_required(error):
    return render_template('401.html'), 401


port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)  # setting host='0.0.0.0' makes the server publicly available

# app.run(port=8083, host='127.0.0.1', debug=True)
