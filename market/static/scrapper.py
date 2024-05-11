import requests
import re

def businessFunc(url):
    import re    
    pattern = r'place/(.*?)/'    
    match = re.search(pattern, url)
    if match:
        business_name = match.group(1)
        return business_name.replace('+',' ')
    else:
        return "Business name not found"


def scrapperFunction(url):
    # Send a GET request to the URL
    headers = {
    'Accept-Language': 'en-US,en;q=0.5'  # English language preference with United States English as the primary language
    }
    response = requests.get(url, headers=headers)

    # businessName = businessFunc(url)

    # Check if the request was successful    
    if response.status_code == 200:        
        scrap = response.text        
        scrap = scrap.replace(',','')
        
        countPattern = "\\d{1,8} reviews"
        match = re.search(countPattern, scrap)
        reviewsCount = int(match.group().split(' ')[0]) if match else None    

        pattern = r'<meta content="([^"]+)" property="og:title">'
        matches = re.findall(pattern, response.text)
        businessName = matches[0].split(' ·')[0] if matches else 'Not Found'

        # reviewPattern = f'null,\d\.\d,{reviewsCount}'
        
        # match1 = re.findall(reviewPattern, response.text)
        # if match1 == []:
        #     reviewPattern = f'null,\d,{reviewsCount}'            
        #     match1 = re.findall(reviewPattern, response.text)            
        # reviews = float(match1[0].split(',')[1]) if match1 else None
        
        return businessName,reviewsCount
    else:
        print("Failed to fetch page:", response.status_code)
        return None,None
    
def form_to_dict(form):
    data = {
        'BusinessName': form.BusinessName.data,
        'URL': form.url.data,
        'ReviewsCount': form.ReviewsCount.data
    }
    return data

def config():
    from market import db
    from market.models import User
    user = User(username = 'admin', password = 'Acord123@', role = 'admin')
    db.session.add(user)
    db.session.commit()