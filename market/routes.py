from flask import render_template,request, flash, redirect, url_for
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

@app.rute('/signup', methods = ['GET'])
def signup_page():
    if request.method == 'GET':
        if User.query.filter_by(username = 'admin').first():
            user = User(username = 'admin', password = 'Acord123@', role = 'admin')
            db.session.add(user)
            db.session.commit()
            return 'Pass'
        else:
            return 'User already Exists.'

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
    import datetime
    
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
        businesses_reviews_dates = {
        (business,ScrapeData.query.filter_by(BusinessName = business).first().URL, ScrapeData.query.filter_by(BusinessName = business).first().NickName): zip(review_count_dict[business], dates) for business in businesses
        }
        
        return render_template('home.html', items = items,businesses = businesses, dates = dates, cols = cols, reviewList = review_count_dict, businesses_reviews_dates = businesses_reviews_dates)
    if request.method == 'POST':
        # return redirect(url_for('home_page'))
        action_type = request.form['actionType']
        changes = json.loads(request.form['changes']) if action_type in ('editDates','editReviews', 'editNickName') else None
        
        if action_type == 'getBusiness':
            business = request.form['business']     
            print(business)
            print(business)
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
        elif action_type == 'delBusiness':
            business = request.form['business']        
            bs = ScrapeData.query.filter_by(BusinessName = business).all()
            for b in bs:
                db.session.delete(b)
            try:
                db.session.commit()
                flash(f'Buusiness Deleted Successfully!', category = 'success')
            except Exception as e:
                db.session.rollback()
                print(e)
                flash(f'Error Occurred while deleting Business', category = 'success')
            return redirect(url_for('home_page'))
        elif action_type == 'delDate':
            date = request.form['date']
            bs = ScrapeData.query.filter_by(Date = date).all()
            for bus in bs:
                db.session.delete(bus)
            try:
                db.session.commit()
                flash(f'Buusiness Deleted Successfully!', category = 'success')
            except Exception as e:
                db.session.rollback()
                print(e)
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
            for business, dates_reviews in changes.items():
                for dateItem, review in dates_reviews.items():
                    data_exist = ScrapeData.query.filter_by(Date=dateItem, BusinessName=business).first()
                    if data_exist:
                        data_exist.ReviewsCount = review
                        db.session.add(data_exist)
                    elif review != '':
                        scrapeData = ScrapeData.query.filter_by(BusinessName=business).first()
                        if scrapeData:
                            dateFormat = dateItem.split('-')
                            newScrape = ScrapeData(URL = scrapeData.URL, BusinessName = business, Date = datetime.date(int(dateFormat[0]), int(dateFormat[1]), int(dateFormat[2])), ReviewsCount = review)
                            db.session.add(newScrape)
            db.session.commit()
            return redirect(url_for('home_page'))
        elif action_type == 'editNickName':
            for business,nickName in changes.items():
                for data in ScrapeData.query.filter_by(BusinessName = business):
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
