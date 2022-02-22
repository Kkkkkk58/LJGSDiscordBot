import requests
from bs4 import BeautifulSoup as BS

URL = 'https://www.anekdot.ru/random/anekdot/'
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
           'accept': '*/*' }

def get_html(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)
    return r

def get_content(html):
    soup = BS(html, 'html.parser')
    items = soup.find('div', class_='text')
    return items

def parse():
    html = get_html(URL)
    if html.status_code == 200:
        items = get_content(html.text)
    else:
        print('Error')
    return items

parse()
