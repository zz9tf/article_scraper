from utils import read_env, proxy_headers
import re
import os
import pandas as pd
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urlencode
from urllib.parse import urlparse
import urllib3
# Disable the warnings for insecure requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from difflib import SequenceMatcher
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import PyPDF2
import magic
import shutil
import string

class scrap:
    def __init__(self, scopus_api_key, verbose=False) -> None:
        
        # load keys
        self.scopus_api_key = scopus_api_key
        
        # get proxies
        self.proxies = proxy_headers._get_proxies()
        self.proxyID = 0
        
        # set up selenium driver
        # self.driver = webdriver.Chrome()
        # self.driver.get("https://www.sciencedirect.com/")
        # self._wait_utill_response(By.CSS_SELECTOR, "#gh-signin-btn > .link-button-text").click()
        # self._wait_utill_response(By.ID, "bdd-email").click()
        # self._wait_utill_response(By.ID, "bdd-email").send_keys(os.getenv('email'))
        # self._wait_utill_response(By.ID, "bdd-email").send_keys(Keys.ENTER)
        # self._wait_utill_response(By.CSS_SELECTOR, ".els-container-right").click()
        # self._wait_utill_response(By.ID, "username").send_keys(os.getenv('email'))
        # self._wait_utill_response(By.ID, "password").send_keys(os.getenv('password'))
        # self._wait_utill_response(By.ID, "password").send_keys(Keys.ENTER)
        # self._wait_utill_response(By.ID, "trust-browser-button").click()
        # self._wait_utill_response(By.NAME, "_eventId_proceed").click()
        
        # set up user header
        self.user_agent = UserAgent()
        
        # response waiting time
        self.waiting_time = 60
        
        # Create folders
        self.root = Path(__file__).parent.parent
        self.save_folder = os.path.join(self.root, 'download')
        self.log_folder = os.path.join(self.root, 'log')
        if not os.path.exists(self.log_folder):
            os.mkdir(self.log_folder)

        self.view_html = os.path.join(self.log_folder, 'view.html')
        self.bad_url_log = open(os.path.join(self.log_folder, 'bad_url'), 'w')

        # set up save length of pdf & txt files
        self.length = 256 - len(os.path.join(self.save_folder, "download_pdf", ".pdf")) - 14

        self.verbose = verbose

    def _wait_utill_response(self, selector, filename):
        field = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((selector, filename))
        )
        return field

    def set_verbose(self, verbose):
        if type(verbose) is bool:
            self.verbose = verbose
        else:
            raise ValueError("Expected boolean value, got %s" % verbose)

    def download_articles(self, inquire_num=None, query=None, start=0, downloaded=0, cursor=False, csv_only=False, results=None, restart=False) -> None:
        """
        Args:
            num (int): The number of articles you want to download.
            query (str): The query you use on google scholar search.
            start (int): The index of articles you want to download.(ie: you want to start the index at where
                you stoped last time). Defualt value is 0.
            downloaded (int): The number of articles you have sucessfully downloaded. It's for calculate how much articles
                you still need to download(ie: inquire_num - downloaded = articles_you_still_need)
            cursor (bool): If you are limited for using '*' in api.
            csv_only (bool): If you just want to download csv file from api(which is more faster and stable)
            results (str): load results.csv locally downloaded from scopus.
            restart (bool): If you want to restart to download articles based on previous index and downloaded articles.
        """
        self.inquire_num = inquire_num
        self.query = query
        self.start = start
        self.downloaded = downloaded

        restart_path = os.path.join(self.log_folder, 'restart_index')
        if restart and os.path.exists(restart_path) and self.start == 0:
            with open(restart_path, 'r') as f:
                js = json.loads(f.read())
                self.start = js['start']
                self.downloaded = js['downloaded']
        
        if self.start == 0:
            self._recreate_save_folder()
        
        if results is None:
            assert inquire_num == None, "Inquire number should be a specific number"
            assert query == None, "query should be a specific string"
 
            self.cursor = '*' if cursor else None  # limit number 5000 if cursor is None
            self.csv_only = csv_only
            
            self._download_articles()
            
        else:
            self._donwload_aticles_based_on_local_csv(results)
        
        # self.driver.quit()
        self.bad_url_log.close()

    def _recreate_save_folder(self):
        """
        Recreate the save folder by deleting it if it already exists and creating a new one.
        
        Returns:
            str: The path of the newly created save folder.
        """
        
        # If the save folder already exists, delete it recursively 
        if os.path.exists(self.save_folder):
            shutil.rmtree(self.save_folder)
        
        os.mkdir(self.save_folder)
        # Create a new empty directory for saving files in pdf format
        os.mkdir(os.path.join(self.save_folder, "download_pdf"))
        
        # Create a new empty directory for saving files in txt format
        os.mkdir(os.path.join(self.save_folder, "download_txt"))
         
        # Print message indicating that folders have been created successfully 
        print("Created folders: {} and its subfolders".format(self.save_folder))

    def _donwload_aticles_based_on_local_csv(self, results):
        df = pd.read_csv(os.path.join(self.log_folder, results))
        if self.inquire_num is None: self.inquire_num = len(df)
        articles = []
        
        i = self.start
        while i < len(df):
            row = df.iloc[i]
            if i >= self.inquire_num:
                break
            title = row['title']
            eid = row['eid']
            
            articles_num_before_download = len(articles)
            
            if self.verbose:
                print("\nDownloading article: %s" % title)
                
            if self._download_single_pdf(title, eid):
                articles.append(title)
            
            success_download_num = len(articles)+self.downloaded
            if len(articles) > articles_num_before_download:
                print("{} | Downloaded ariticles {}({}) {:.2f}% | {}".format(i+1, success_download_num, self.inquire_num
                                                                             , 100*success_download_num/(i+1)
                                                                             , self._remove_between_tags(title)))
            else:
                print("{} | Article not found: {}({}) {:.2f}% | {}".format(i+1, success_download_num, self.inquire_num
                                                                             , 100*success_download_num/(i+1)
                                                                             , self._remove_between_tags(title)))
            with open(os.path.join(self.log_folder, 'restart_index'), 'w') as f:
                f.write(json.dumps({'start': i, 'downloaded': success_download_num}, indent=4))
            
            i += 1

    def _download_articles(self):
        articles = []
        scopus_results = []
        limit_num = 5000 if self.cursor is None else 0
        self.count_num = 200
        # loop to download pdf link
        i = self.start
        while True:
            if i != self.start and i >= limit_num:
                # No more articles to get
                print("No more articles to get!")
                break
            if len(articles) > self.inquire_num or (self.cursor is not None and i > self.inquire_num):
                # I get enough articles
                print("Get enough articles!")
                break

            js = self._search_article_names_from_scopus(i)
            if js is None:
                input("Something wrong with search article")
            entries = js['search-results']['entry']
            scopus_results += [self._parse_article(entry) for entry in entries]
            pd.DataFrame(scopus_results).to_csv(os.path.join(self.log_folder, 'result.csv'))
            
            if limit_num == self.start:
                limit_num = self._get_maximun_limitation_of_aritlces(js)
            
            if self.csv_only:
                print("Downloaded: {:.2f}%({}/{}) | Remain usage: {}".format(
                    (i+25)/self.inquire_num*100, i+25, self.inquire_num, self.remain_usage))
                if self.cursor != None:
                    with open(os.path.join(self.log_folder, 'next_cursor'), 'w') as f:
                        f.write(self.cursor)
            else:
                self._download_articles_based_on_search(js, i, articles)
                
            i += self.count_num

    def _search_article_names_from_scopus(self, index):
        '''
            Search Scopus database using key as api key, with query.

            Parameters
            ----------
            index : int
                Start index.

            Returns
            -------
            js: dict
                A json file download from scopus api
        '''
        if self.cursor is None:
            par = {'apikey': self.scopus_api_key, 'query': self.query, 'start': index,
                'httpAccept': 'application/json', 'view': 'STANDARD', 'count': str(self.count_num),
                }
        elif self.cursor == '*':
            par = {'apikey': self.scopus_api_key, 'query': self.query, 'start': index, "cursor": self.cursor, 
                'httpAccept': 'application/json', 'view': 'STANDARD',  'count': str(self.count_num),
                }
        else:
            par = {'apikey': self.scopus_api_key, 'query': self.query, "cursor": self.cursor, 
                'httpAccept': 'application/json', 'view': 'STANDARD', 'count': str(self.count_num),
                }
        r = requests.get("https://api.elsevier.com/content/search/scopus", params=par)
        
        self.remain_usage = r.headers['X-RateLimit-Remaining']
        
        js = r.json()
        if self.cursor is not None:
            self.cursor = js['search-results']['cursor']['@next']
            
        with open(self.view_html, "w") as f:
            json.dumps(js, f, indent=4)
        
        if 'service-error' in js.keys():
            # No articles founded
            print("you get service-error")
            return None
 
        return js

    def _parse_article(self, entry):
        try:
            scopus_id = entry['dc:identifier'].split(':')[-1]
        except:
            scopus_id = None
        try:
            title = entry['dc:title']
        except:
            title = None
        try:
            publicationname = entry['prism:publicationName']
        except:
            publicationname = None
        try:
            issn = entry['prism:issn']
        except:
            issn = None
        try:
            isbn = entry['prism:isbn']
        except:
            isbn = None
        try:
            eissn = entry['prism:eIssn']
        except:
            eissn = None
        try:
            volume = entry['prism:volume']
        except:
            volume = None
        try:
            pagerange = entry['prism:pageRange']
        except:
            pagerange = None
        try:
            coverdate = entry['prism:coverDate']
        except:
            coverdate = None
        try:
            doi = entry['prism:doi']
        except:
            doi = None
        try:
            citationcount = int(entry['citedby-count'])
        except:
            citationcount = None
        try:
            affiliation = self._parse_affiliation(entry['affiliation'])
        except:
            affiliation = None
        try:
            aggregationtype = entry['prism:aggregationType']
        except:
            aggregationtype = None
        try:
            sub_dc = entry['subtypeDescription']
        except:
            sub_dc = None
        try:
            author_entry = entry['author']
            author_id_list = [auth_entry['authid'] for auth_entry in author_entry]
        except:
            author_id_list = list()
        try:
            link_list = entry['link']
            scopus_link = None
            for link in link_list:
                if link['@ref'] == 'full-text':
                    scopus_link = link['@href']
        except:
            scopus_link = None
        try:
            eid = scopus_link.split('/')[-1]
        except:
            eid = None
            
        return pd.Series({'scopus_id': scopus_id, 'eid': eid, 'title': title, 'publication_name':publicationname,\
            'issn': issn, 'isbn': isbn, 'eissn': eissn, 'volume': volume, 'page_range': pagerange,\
            'cover_date': coverdate, 'doi': doi,'citation_count': citationcount, 'affiliation': affiliation,\
            'aggregation_type': aggregationtype, 'subtype_description': sub_dc, 'authors': author_id_list,\
            'full-text': scopus_link})

    def _parse_affiliation(self, js_affiliation):
        l = list()
        for js_affil in js_affiliation:
            name = js_affil['affilname']
            city = js_affil['affiliation-city']
            country = js_affil['affiliation-country']
            l.append({'name': name, 'city': city, 'country': country})
        return l

    def _get_maximun_limitation_of_aritlces(self, js):
        # Get maximum num of articles I can get
        limit_num = int(js['search-results']['opensearch:totalResults'])
        print("You can have at most {} articles".format(limit_num))
        return limit_num

    def _download_articles_based_on_search(self, js, i, articles):
        entries = js['search-results']['entry']
        results = pd.DataFrame([self._parse_article(entry) for entry in entries])
        
        # Go over all articles I get in one turn scopus search
        for i, row in results[['title', 'eid']].iterrows():
            title = row['title']
            eid = row['eid']
            
            num_articles = len(articles)
            success_download_num = len(articles)+self.downloaded
            
            if self.verbose:
                print("Downloading article: %s" % title)
                print("{} | Getting ariticles {}({}) {:.2f}% | {}".format(i, success_download_num, self.inquire_num
                                                                          , 100*(success_download_num)/self.inquire_num
                                                                          , self._remove_between_tags(title)))
            if self._download_single_pdf(title, eid):
                articles.append(title)

            if not self.verbose:
                if len(articles) > num_articles:
                    print("{} | Downloaded ariticles {}({}) {:.2f}% | {}".format(i, success_download_num, self.inquire_num
                                                                                 , 100*success_download_num/self.inquire_num
                                                                                 , self._remove_between_tags(title)))
                else:
                    print("{} | Article not found: {}".format(i, title))

    def _download_single_pdf(self, title, eid):
        title = self._remove_between_tags(title)
        downloaded = False
        log = '\nTitle: ' + title + '\n'
        
        if eid is not pd.NA:
            if self.verbose:
                print(">>> eid <<<")
            # Get pdf from science direct eid
            link = 'https://api.elsevier.com/content/article/eid/{}-am.pdf'.format(eid)
            params = { 'httpAccept': 'application/pdf', 'apiKey': os.getenv('scopus_api_key') }
            r = self._response_based_on_request(link, params=params)
            if r is not None and self._save_file(title, r):
                return True
            else:
                link = link + "?" + urlencode(params)
                log += 'eid: ' + link + '\n'
                if self.verbose:
                    print("Not success url: ", link)
            
        # Get link from google scholar
        link = "https://scholar.lanfanshu.cn/scholar"
        params = { 'q': title }
        headers = {'User-Agent': self.user_agent.random}
        r = self._response_based_on_request(link, params=params, headers=headers)
        if r is not None and r.status_code < 200 or r.status_code > 300:
            link = link + "?" + urlencode(params)
            log += 'google scholar: ' + r.url + '\n'
            if self.verbose:
                print("Non success url: ", link)
            self.bad_url_log.write(log)
            return False
        
        soup = BeautifulSoup(r.content, 'html.parser')
        # Get link from google scholar
        articles = []
        elements = soup.find_all("h3", {"class": "gs_rt"})
        for e in elements:
            for link in e.find_all('a'):
                if SequenceMatcher(None, title, link.text).ratio() > 0.5:
                    articles.append({'title': title, 'link': link.get('href')})
        
        # Search pdf link from article search result
        for article in articles:
            if downloaded:
                break
            
            if self._extract_domain_name(article['link']) == "www.sciencedirect.com":
                if self.verbose:
                    print(">>> sciencedirect <<<")
                # Go pdf from sciencedrict
                pii = article['link'].split('/')[-1]
                link = 'https://api.elsevier.com/content/object/pii/{}'.format(pii)
                params = { 'apiKey': os.getenv('scopus_api_key'), 'httpAccept':'application/json' }
                # Get pdf link from api
                r = self._response_based_on_request(link, params=params, save_js=True)
                if r is None: continue
                new_link = self._get_link_from_js(r.json())
                if new_link is None:
                    # I didn't get valid pdf link from api
                    continue
                link = new_link
                # Get PDF file from pdf link
                params = { 'httpAccept': 'application/pdf', 'apiKey': os.getenv('scopus_api_key') }
                r = self._response_based_on_request(link, params=params)
                if r is not None and self._save_file(article['title'], r):
                    downloaded = True
                else:
                    link = link + "?" + urlencode(params)
                    log += 'sciencedirect: ' + link + '\n'
                    if self.verbose:
                        print("Not success url: ", link)
            
            elif re.search(r'\bpdf\b', article['link'], re.I):
                if self.verbose:
                    print(">>> google scholar <<<")
                # Get pdf from google scholar
                link = article['link']
                r = self._response_based_on_request(link)
                if r is not None and self._save_file(article['title'], r):
                    downloaded = True
                else:
                    log += 'google pdf: ' + link + '\n'
                    if self.verbose:
                        print("Not success url: ", prefix + link.get('href'))
            
            else:
                if self.verbose:
                    print(">>> other websites <<<")
                # Get pdf link from other websites | Deep search
                link = article['link']
                r = self._response_based_on_request(link, headers=headers)
                if r is not None and r.status_code < 200 or r.status_code > 300:
                    log += 'other: ' + link + '\n'
                    if self.verbose:
                        print("Not success url: ",  link)
                    continue
                
                soup = BeautifulSoup(r.content, 'html.parser')
                pdf_links = soup.find_all('a', href=lambda href: href and re.search(r'\bpdf\b', href, re.I))
                # Get PDF file from pdf link
                for link in pdf_links:
                    if downloaded:
                        break
                    parsed_link = urlparse(link.get('href'))
                    if bool(parsed_link.scheme and parsed_link.netloc):
                        link = link.get('href')
                    else:
                        prefix = "https://" + self._extract_domain_name(article['link'])
                        link = prefix + link.get('href')
                    if self.verbose:
                        print(">>> {} <<<".format(self._extract_domain_name(article['link'])))
                    r = self._response_based_on_request(link, headers=headers)
                    if r is not None and self._save_file(title, r):
                        downloaded = True
                    else:
                        log += 'other pdf: ' + r.url + '\n'
                        if self.verbose:
                            print("Not success url: ", link)
        if downloaded:
            return True
        else:
            self.bad_url_log.write(log)
            return False
    
    def _response_based_on_request(self, link, headers=None, params=None, save_js=False):
        try:
            if self.verbose:
                if params is not None:
                    print("search:", link + "?" + urlencode(params))
                else:
                    print("search:", link)
            # Get response from url
            if headers == None and params == None:
                r = requests.get(link, timeout=self.waiting_time, verify=False)
            elif headers == None:
                r = requests.get(link, params=params, timeout=self.waiting_time, verify=False)
            elif params == None:
                r = requests.get(link, headers=headers, timeout=self.waiting_time, verify=False)
            else:
                r = requests.get(link, headers=headers, params=params, timeout=self.waiting_time, verify=False)
            if r.status_code >= 200 and r.status_code <= 300:
                if not save_js:
                    with open(self.view_html, 'wb') as f:
                        f.write(r.content)
                else:
                    js = r.json()
                    with open(self.view_html, 'w') as f:
                        json.dump(js, f, indent=4)

            if self.verbose:
                print(r.status_code)
            
            return r
        except Exception as e:
            print(e)
            return None
    
    def _get_link_from_js(self, js):
        result = js['choices']['choice']
        if type(result) == dict:
            if result['@type'] == 'AAM-PDF':
                return result['$']
        else:
            for url in result:
                if url['@type'] == 'AAM-PDF':
                    return url['$']
        return None
    
    def _remove_between_tags(self, string):
        pattern = r"<[^>]+>"
        result = re.sub(pattern, "", string)
        return result

    def _extract_domain_name(self, url):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        return domain

    def _save_file(self, title, r):
        """
        Save a file to pdf format and text format
        
        Params:
            name: String, the name of the file
            r: response get from url request
        
        Return:
            None
        """
        if magic.from_buffer(r.content, mime=True) != 'application/pdf':
            return False
        # Get the right name
        valid_chars = "-_.(), %s%s" % (string.ascii_letters, string.digits)
        title = ''.join(c if c in valid_chars else '' for c in title)[:self.length]
        i = 1
        ori_name = title

        while os.path.exists(os.path.join(self.save_folder, "download_pdf", title + ".pdf")):
            title = "{}({})".format(ori_name, str(i))
            i += 1

        pdf_path = os.path.join(self.save_folder, "download_pdf", title + ".pdf")
        txt_path = os.path.join(self.save_folder, "download_txt", title + ".txt")

        # Write pdf file
        if self.verbose:
            print("Saving pdf file: {}".format(title))
        
        with open(pdf_path, 'wb') as pdf:
            pdf.write(r.content)

        # Write txt file
        if self.verbose:
            print("Saving txt file: {}".format(title))
        with open(txt_path, "w", encoding='utf-8') as file:
            reader = PyPDF2.PdfReader(pdf_path, strict=False)
            for page in reader.pages:
                content = page.extract_text()
                file.write(content + '\n')
        return True

if __name__ == '__main__':
    # set up
    # s = scrap(os.getenv('scopus_api_key'))
    # s.set_verbose(True)
    # s._recreate_save_folder()
    # df = pd.read_csv(os.path.join(s.log_folder, 'monosaccharides.csv'))
    # for row in df['title']:
    #     title = s._remove_between_tags(row)
    #     s._download_single_pdf(title)
    
    # content = open("../log/view.html", 'rb')
    # soup = BeautifulSoup(content, 'html.parser')
    # elements = soup.find_all("h3", {"class": "gs_rt"})
    # for e in elements:
    #     for link in e.find_all('a'):
    #         href = link.get('href')
    #         print(href)
        # href = link.get('href')
        # if type(href) is str and "https://" in href:
        #     print(href)
    
    # url = 'https://www.nature.com/articles/s41467-023-37365-4'
    user_agent = UserAgent()
    headers = {'User-Agent': user_agent.random}
    # r = requests.get(url, headers=headers)
    # with open('../log/view.html', 'wb') as f:
    #     f.write(r.content)
    r = requests.get("https://www.sciencedirect.com/science/article/pii/S2667025923000201", headers=headers)
    print(r.status_code)