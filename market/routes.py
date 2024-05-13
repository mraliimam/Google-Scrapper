from flask import render_template,request, flash, redirect, url_for
from market import app
from market.models import *
from market.forms import *
from flask_login import logout_user, current_user, login_required
from flask_login import login_user
from functools import wraps
from market.static.scrapper import *


def auth(form):
    user = User.query.filter_by(username = form.username.data).first()
    if user and user.check_password_correction(attempted_password = form.password.data):
        login_user(user)
        return 'Pass'
    else:
        return 'Fail'

def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                flash("You are not authorized to access this page.", category = "danger")
                return redirect(url_for("home_page"))
            return f(*args, **kwargs)
        return wrapped
    return wrapper

@app.route('/login', methods = ['GET', 'POST'])
def login_page():

    form = LoginForm()

    if request.method == 'GET':
        return render_template('login.html', form = form)

    if request.method == 'POST':
        if auth(form) == 'Pass':            
            return redirect(request.args.get('next') or url_for('home_page'))
        else:
            flash('Wrong Username or Password', category='danger')
            return redirect(url_for('login_page'))
            
@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash('User is logout Successfuly!!', category='info')
    return redirect(url_for('login_page'))


@app.route('/', methods = ['GET', 'POST'])
@app.route('/home', methods = ['GET', 'POST'])
@login_required
def home_page():
    from datetime import date
    
    if request.method == 'GET':
        items = ScrapeData.query.all()
        businesses = set(result.BusinessName for result in items)
        dates = sorted(set(result.Date for result in items))
        review_count_dict = {business: [''] * len(dates) for business in businesses}

        for item in items:
            business = item.BusinessName
            date_index = dates.index(item.Date)
            review_count_dict[business][date_index] = item.ReviewsCount
        
        cols = ScrapeData.__table__.columns.keys()
        return render_template('home.html', items = items,businesses = businesses, dates = dates, cols = cols, reviewList = review_count_dict)
    if request.method == 'POST':
        business = request.form['business']        
        url = ScrapeData.query.filter_by(BusinessName = business).first().URL
        businessName, reviewsCount = scrapperFunction(url)
        dataExist = ScrapeData.query.filter_by(Date = date.today(), URL = url).first()
        if dataExist:
            dataExist.ReviewsCount = reviewsCount
            db.session.add(dataExist)
            db.session.commit()
        else:            
            data = ScrapeData(URL = url, BusinessName = businessName, ReviewsCount = reviewsCount)
            db.session.add(data)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Exception occurs: {e}!!', category='danger')
        return redirect(url_for('home_page'))

@app.route('/data')
@login_required
def data_page():
    businessName = request.args.get('name')
    items = ScrapeData.query.filter_by(BusinessName = businessName)
    return render_template('data.html', items = items, businessName = businessName)

@app.route('/form', methods = ['GET', 'POST'])
@login_required
def form_page():

    from datetime import date

    form = BusinessForm()
    
    if request.method == 'GET':
        return render_template('form.html', form = form)
    
    if request.method == 'POST':        
        
        form.BusinessName.data, form.ReviewsCount.data = scrapperFunction(form.url.data)        
        
        if None in (form.BusinessName.data, form.ReviewsCount.data):
            flash('Data cannot be scrapped!', category='danger')
            return redirect(url_for('form_page'))
        
        else:
            dataExist = ScrapeData.query.filter_by(Date = date.today(), URL = form.url.data).first()
            if dataExist:
                dataExist.ReviewsCount = form.ReviewsCount.data
                db.session.add(dataExist)
                db.session.commit()
            else:
                data = ScrapeData(**form_to_dict(form))
                db.session.add(data)
                try:
                    db.session.commit()
                    flash('Data is added Successfuly!!', category='success')
                    return redirect(url_for('home_page'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Exception occurs: {e}!!', category='danger')
                    return redirect(url_for('form_page'))