from flask import render_template,request, flash, redirect, url_for, send_file
import os
from market import app
from market.models import *
from market.forms import *
from flask_login import logout_user, current_user, login_required
from flask_login import login_user
from functools import wraps
from market.static.scrapper import *
import json

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

@app.route('/signup', methods = ['GET'])
def signup_page():
    if request.method == 'GET':
        if User.query.filter_by(username = 'admin').first():
            return 'User already Exists.'
        else:
            user = User(username = 'admin', password = 'Acord123@', role = 'admin')
            db.session.add(user)
            db.session.commit()
            return 'Pass'

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


@app.route('/download-db', methods=['GET'])
@login_required
def download_db():

    db_path = os.path.join(app.root_path, 'scrapper.db')
    if os.path.exists(db_path):
        return send_file(db_path, as_attachment=True)
    else:
        flash('Database file not found.', category='danger')
        return redirect(url_for('home_page'))


@app.route('/', methods = ['GET', 'POST'])
@app.route('/home', methods = ['GET', 'POST'])
@login_required
def home_page():
    from datetime import datetime
    import pytz
    new_york_date = datetime.now(pytz.timezone('America/New_York')).date()
    import datetime
    
    if request.method == 'GET':
        items = ScrapeData.query.all()
        urlOfBusinesses = set(result.URL for result in items)
        dates = sorted(set(result.Date for result in items))
        review_count_dict = {business: [''] * len(dates) for business in urlOfBusinesses}

        for item in items:
            urls = item.URL
            date_index = dates.index(item.Date)
            review_count_dict[urls][date_index] = item.ReviewsCount
        
        cols = ScrapeData.__table__.columns.keys()
        businesses_reviews_dates = {
        (ScrapeData.query.filter_by(URL = url).first().BusinessName,ScrapeData.query.filter_by(URL = url).first().URL, ScrapeData.query.filter_by(URL = url).first().NickName): zip(review_count_dict[url], dates) for url in urlOfBusinesses
        }
        
        return render_template('home.html', items = items, dates = dates, cols = cols, reviewList = review_count_dict, businesses_reviews_dates = businesses_reviews_dates)
    if request.method == 'POST':
        # return redirect(url_for('home_page'))
        action_type = request.form['actionType']
        changes = json.loads(request.form['changes']) if action_type in ('editDates','editReviews', 'editNickName') else None
        
        if action_type == 'getBusiness':
            url = request.form['business']   

            if ScrapeData.query.filter_by(URL = url).first():
                businessName, reviewsCount = scrapperFunction(url)
                dataExist = ScrapeData.query.filter_by(Date = new_york_date, URL = url).first()
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
            else:
                flash(f'URL NO FOUND!!', category='danger')
            return redirect(url_for('home_page'))
        elif action_type == 'delBusiness':
            url = request.form['business']        
            bs = ScrapeData.query.filter_by(URL = url).all()
            for b in bs:
                db.session.delete(b)
            try:
                db.session.commit()
                flash(f'Buusiness Deleted Successfully!', category = 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error Occurred while deleting Business', category = 'success')
            return redirect(url_for('home_page'))
        elif action_type == 'delDate':
            date = request.form['date']
            bs = ScrapeData.query.filter_by(Date = date).all()
            for bus in bs:
                db.session.delete(bus)
            try:
                db.session.commit()
                flash(f'Date Deleted Successfully!', category = 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error Occurred while deleting Business', category = 'success')
            return redirect(url_for('home_page'))
        elif action_type == 'editDates':
            for original_date, new_date in changes.items():
                if original_date != new_date:
                    items = ScrapeData.query.filter_by(Date=original_date).all()
                    for item in items:
                        dateFormat = new_date.split('-')
                        item.Date = datetime.date(int(dateFormat[2]), int(dateFormat[0]), int(dateFormat[1]))
                        db.session.add(item)
            db.session.commit()
            return redirect(url_for('home_page'))
        elif action_type == 'editReviews':
            for url, dates_reviews in changes.items():
                for dateItem, review in dates_reviews.items():
                    data_exist = ScrapeData.query.filter_by(Date=dateItem, URL=url).first()
                    if data_exist:
                        data_exist.ReviewsCount = review
                        db.session.add(data_exist)
                    elif review != '':
                        scrapeData = ScrapeData.query.filter_by(URL=url).first()
                        if scrapeData:
                            dateFormat = dateItem.split('-')
                            newScrape = ScrapeData(URL = scrapeData.URL, BusinessName = scrapeData.BusinessName, Date = datetime.date(int(dateFormat[0]), int(dateFormat[1]), int(dateFormat[2])), ReviewsCount = review)
                            db.session.add(newScrape)
            db.session.commit()
            return redirect(url_for('home_page'))
        elif action_type == 'editNickName':
            for url,nickName in changes.items():
                for data in ScrapeData.query.filter_by(URL = url):
                    data.NickName = nickName if nickName else ''
                    db.session.add(data)
            db.session.commit()
            return redirect(url_for('home_page'))
        else:
            flash('Invalid action type', category='danger')
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

    from datetime import datetime
    import pytz
    new_york_date = datetime.now(pytz.timezone('America/New_York')).date()

    form = BusinessForm()
    
    if request.method == 'GET':
        return render_template('form.html', form = form)
    
    if request.method == 'POST':        
        
        form.BusinessName.data, form.ReviewsCount.data = scrapperFunction(form.url.data)        
        
        if None in (form.BusinessName.data, form.ReviewsCount.data):
            if form.BusinessName.data:
                form.ReviewsCount.data = 0
            else:
                flash('Data cannot be scrapped!', category='danger')
                return redirect(url_for('form_page'))        
        
        dataExist = ScrapeData.query.filter_by(Date = new_york_date, URL = form.url.data).first()
        if dataExist:
            dataExist.ReviewsCount = form.ReviewsCount.data
            db.session.add(dataExist)
            db.session.commit()
            return redirect(url_for('form_page'))
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
            
@app.route('/getAllReviews')
def get_reviews():

    from datetime import datetime
    import pytz
    new_york_date = datetime.now(pytz.timezone('America/New_York')).date()

    items = ScrapeData.query.all()
    urlOfBusinesses = set(result.URL for result in items)

    for url in urlOfBusinesses:
        businessName,reviewsCount = scrapperFunction(url)
        if None in (businessName, reviewsCount):
            if businessName:
                reviewsCount = 0
            else:
                # flash('Data cannot be scrapped!', category='danger')
                # db.session.rollback()
                # return redirect(url_for('home_page'))
                continue
        dataExist = ScrapeData.query.filter_by(Date = new_york_date, URL = url).first()
        if dataExist:
            dataExist.ReviewsCount = reviewsCount
            db.session.add(dataExist)
            db.session.commit()
            return redirect(url_for('form_page'))
        else:
            data = ScrapeData(BusinessName = businessName, URL = url,ReviewsCount = reviewsCount, Date = new_york_date)
            db.session.add(data)
    try:
        db.session.commit()
        flash('Data is added Successfuly!!', category='success')
        return redirect(url_for('home_page'))
    except Exception as e:
        db.session.rollback()
        flash(f'Exception occurs: {e}!!', category='danger')
        return redirect(url_for('home_page'))