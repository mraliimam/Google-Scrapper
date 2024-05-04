import requests
import re

def scrapperFunction(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:        
        scrap = response.text        
        scrap = scrap.replace(',','')
        
        countPattern = "\\d{1,8} reviews"
        match = re.search(countPattern, scrap)
        reviewsCount = int(match.group().split(' ')[0]) if match else None

        reviewPattern = f'null,\d\.\d,{reviewsCount}'
        
        match1 = re.findall(reviewPattern, response.text)
        if match1 == []:
            reviewPattern = f'null,\d,{reviewsCount}'            
            match1 = re.findall(reviewPattern, response.text)            
        reviews = float(match1[0].split(',')[1]) if match1 else None
        
        return reviews,reviewsCount
    else:
        print("Failed to fetch page:", response.status_code)
        return None,None
    
def form_to_dict(form):
    data = {
        'BusinessName': form.BusinessName.data,
        'URL': form.url.data,
        'ReviewsCount': form.ReviewsCount.data,
        'Review': form.Review.data
    }
    return data

def config():
    from market import db
    from market.models import User
    user = User(username = 'admin', password = 'Acord123@', role = 'admin')
    db.session.add(user)
    db.session.commit()