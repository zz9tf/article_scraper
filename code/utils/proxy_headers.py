from utils import read_env, helper_function
import os
import requests
import time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def _get_proxies():
    """
        Returns:
            a list of available proxies dictionary with formatting
                {
                    'http': http_proxy,
                    'https': https_proxy
                }

    """
    proxies = []
    r = requests.get(os.getenv('LOAD_PROXY'))
    for proxy in r.text.split('\n'):
        if len(proxy) > 0:
            p = proxy.rstrip('\r').split(':')
            proxies.append({
                "http": "http://{}:{}@{}:{}".format(p[2], p[3], p[0], p[1]),
                "https": "http://{}:{}@{}:{}".format(p[2], p[3], p[0], p[1])
            })
    return proxies

def _check_proxy_without_headers(proxies):
    """
        Check if proxy is valid without headers
    """
    counter = 0
    proxy_headers = {}
    for p in proxies:
        # Don't need to show the web page
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Set headless mode
        driver = webdriver.Chrome(seleniumwire_options=p, options=chrome_options)
        driver.get("https://www.openstreetmap.org/about")
        r = driver.page_source
        soup = BeautifulSoup(r, 'html.parser')
        with open('view.html', 'w') as f:
            f.write(soup.prettify())
        
        # Get header 1(A easy header)
        if 'OpenStreetMap' != soup.title.contents[0]:
            print("Blocked with OpenStreetMap: {}".format(str(p)))
        else:
            h = None
            for r in driver.requests:
                if "https://www.openstreetmap.org/about" == str(r):
                    h = {key: value for key, value in r.headers.items()}
            if h != None:
                option = {'proxy': p, 'headers': h}
                driver = webdriver.Chrome(seleniumwire_options=option, options=chrome_options)
                driver.get("https://scholar.google.com/scholar?start=120&q=Monosaccharide&hl=en&as_sdt=0,22")
                r = driver.page_source
                soup = BeautifulSoup(r, 'html.parser')
                with open('view.html', 'w') as f:
                    f.write(soup.prettify())
                if len(r) < 50000:
                    print("Blocked with Google scholar: {}".format(str(p)))
                    # driver = webdriver.Chrome(seleniumwire_options=option)
                    # driver.get("https://scholar.google.com/scholar?start=120&q=Monosaccharide&hl=en&as_sdt=0,22")
                    input()
                else:
                    # Get header 2(A header for google scholar)
                    for r in driver.requests:
                        if "https://scholar.google.com/scholar?start=120&q=Monosaccharide&hl=en&as_sdt=0,22" == str(r):
                            h = {key: value for key, value in r.headers.items()}
                    r = requests.get("https://scholar.google.com/scholar?start=120&q=Monosaccharide&hl=en&as_sdt=0,22", proxies=p, headers=h)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    with open('view.html', 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    # Get effective response
                    if len(r.content) > 50000:
                        proxy_headers[str(p)] = h
                        counter += 1
                        print("Success: {}/{}".format(counter, len(proxies)), end='\r')
        driver.close()
    return proxy_headers

def _check_proxy_with_headers(proxy_with_headers):
    counter = 0
    proxy_headers = {}
    for p in proxy_with_headers:
        r = requests.get("https://scholar.google.com/scholar?start=90&q=Monosaccharide&hl=en&as_sdt=0,22", proxies=eval(p), headers=proxy_with_headers[p].to_dict())
        soup = BeautifulSoup(r.content, 'html.parser')
        with open('view.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        if len(r.content) > 50000:
            proxy_headers[str(p)] = proxy_with_headers[str(p)].to_dict()
            counter += 1
            print("Success: {}/{}".format(counter, len(proxy_with_headers.columns)), end='\r')
    return proxy_headers

def get_proxy_and_headers(proxy_and_headers_file):
    print("Start at {}".format(datetime.now().strftime('%d-%b-%Y %H:%M:%S')))
    start_time = time.time()

    proxy_headers = _get_headers_locally(proxy_and_headers_file)
    if proxy_headers is None:
        print("No header offered!")
        proxy_headers = _check_proxy_without_headers(_get_proxies())
    else:
        proxy_headers = _check_proxy_with_headers(proxy_headers)
    proxy_headers = pd.DataFrame(proxy_headers)
    proxy_headers.to_csv('headers.csv')
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print('Elapsed time:', elapsed_time, 'seconds')
    if elapsed_time < 1:
        time.sleep(1 - elapsed_time)
        print("Implement at least one second now.")
    return proxy_headers

def _get_headers_locally(header_file):
    """
        Loads the headers from a local file
        Params:
            header_file: string
        Returns:
            proxy_headers: dict, None if file is not found
    """
    proxy_headers = None
    if os.path.exists(header_file):
        proxy_headers = pd.read_csv(header_file, index_col=0)
        print('File {} loaded!'.format(header_file))
    else:
        print('File {} not found'.format(header_file))
    
    return proxy_headers


def single_proxy_and_header(view_html='view.html', index=0):
    p = _get_proxies()[index]
    h = eval(os.getenv('header'))

    return p, h

if __name__ == '__main__':
    # Test if I can get the proxy
    proxys = _get_proxies()
    helper_funtion.view_proxys(proxys)

    # Test if I can get a good header with proxy
