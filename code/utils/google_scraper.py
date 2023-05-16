from utils import read_env, helper_funtion
import re
import os
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import PyPDF2
import shutil
import string
from seleniumwire import webdriver
from utils.proxy_headers import get_proxy_and_headers, single_proxy_and_header

class scrap:
    def __init__(self, save_folder='download', log_folder='log', verbose=False, single_proxy=True) -> None:
        
        self.root = Path(__file__).parent.parent
        self.save_folder = os.path.join(self.root, save_folder)
        self.log_folder = os.path.join(self.root, log_folder)
        if not os.path.exists(self.log_folder):
            os.mkdir(self.log_folder)

        self.proxy_and_headers_file = os.path.join(self.log_folder, 'headers.csv')
        self.view_html = os.path.join(self.log_folder, 'view.html')
        self.verbose = verbose
        self.single_proxy = single_proxy
        if single_proxy:
            self.p,  self.h = single_proxy_and_header(self.view_html)
        self.sep = os.path.sep

    def set_verbose(self, verbose):
        if type(verbose) is bool:
            self.verbose = verbose
        else:
            raise ValueError("Expected boolean value, got %s" % verbose)

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

        return self.save_folder

    def _save_file(self, name, r):
        """
        Save a file to pdf format and text format
        
        Params:
            name: String, the name of the file
            r: response get from url request
        
        Return:
            None
        """
        # Get the right name
        valid_chars = "-_.(), %s%s" % (string.ascii_letters, string.digits)
        name = ''.join(c if c in valid_chars else '--' for c in name).strip('-')
        i = 1
        ori_name = name

        while os.path.exists(self.save_folder + self.sep + "download_pdf" + self.sep + name + ".pdf"):
            name = "{}({})".format(ori_name, str(i))
            i += 1

        pdf_path = self.save_folder + self.sep + "download_pdf" + self.sep + name + ".pdf"
        txt_path = self.save_folder + self.sep + "download_txt" + self.sep + name + ".txt"

        # Write pdf file
        if self.verbose:
            print("Saving pdf file: {}".format(name))
        pdf = open(pdf_path, 'wb')
        pdf.write(r.content)
        pdf.close()

        # Write txt file
        if self.verbose:
            print("Saving txt file: {}".format(name))
        file = open(txt_path, "w", encoding='utf-8')
        reader = PyPDF2.PdfReader(pdf_path, strict=False)
        for page in reader.pages:
            content = page.extract_text()
            file.write(content + '\n')
        file.close()

    def _download_single_pdf(self, title, url):
        # Normal get request
        try:
            r_url = requests.get(url)
        except:
            r_url = None
        
        # sci-hub get request
        try:
            r_sci_hub = requests.get('https://sci-hub.ru/{}'.format(url))
            
            with open(self.view_html, 'wb') as f:
                f.write(r_sci_hub.content)
                r_sci_hub = BeautifulSoup(r_sci_hub.content, 'html.parser')
            
            if len(r_sci_hub.findAll("div", {"class":"content"})) != 0:
                r_sci_hub = None
            else:
                url = r_sci_hub.button['onclick'].split("'")[1]
                if "sci-hub" in url:
                    url = "https:" + url
                else:
                    url = "https://sci-hub.ru"+url
                r_sci_hub = requests.get(url)
        except:
            r_sci_hub = None
        
        # Judge which one is successful
        if r_url is not None and len(r_url.content) > 4 and r_url.content[:4] == "%PDF".encode('ascii'):
            # Get pdf from url
            if self.verbose:
                print("normal: " + r_url.url)
            r = r_url
        elif r_sci_hub is not None and len(r_sci_hub.content) > 4 and r_sci_hub.content[:4] == "%PDF".encode('ascii'):
            # Get pdf from sci-hub
            if self.verbose:
                print("sci-hub: " + r_sci_hub.url)
            r = r_sci_hub
        else:
            if self.verbose:
                try:
                    print("url: \n" + str(r_url.status_code))
                except:
                    print("url: \n" + str(r_url))
                try:
                    print("sci-hub: \n" + r_sci_hub.findAll("div", {"class":"content"}))       
                except:
                    print("sci-hub: \n" + str(r_sci_hub))
                
                print("Article not found: {}".format(title))
            return False
        self._save_file(title, r)
        
        return True

    def _set_up_proxy_and_header(self, index=0):
        """
        Setup proxy and header with given index

        Args:
            index (int): An integer that specifies the index of proxy and header to use

        Returns:
            p: str, the proxy
            h: dict, the header
        """
        if not self.single_proxy:
            # set proxy
            p = eval(self.proxy_and_headers.columns[index%len(self.proxy_and_headers.columns)])
            # set header
            h = self.proxy_and_headers[str(p)].to_dict()

            # Verify my ip
            response = requests.get(os.getenv('verify_ip'), proxies=p, headers=h)
            ip_address = response.json()['origin']
            print("Download by ip: {}".format(ip_address))
        else:
            p, h = self.p, self.h

        return p, h

    def _search_article_names_from_google(self, i, p, h):
        # Get search result
        r = requests.get("https://scholar.google.com/scholar?start={}&q={}&hl=en&as_sdt=0,22".format(i, self.query), proxies=p, headers=h)
        if self.single_proxy:
            time.sleep(1)
        else:
            time.sleep(round(2/len(self.proxy_and_headers.columns), 4))

        print('Get url: https://scholar.google.com/scholar?start={}&q={}&hl=en&as_sdt=0,22'.format(i, self.query))
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Record the finnal response
        with open(self.view_html, 'wb') as f:
            f.write(r.content)
        # Get invalid response then drop this proxy
        try:
            # server_error = soup.body.find(id='gs_md_err').contents[0]
            server_error = None
        except:
            server_error = None
        if len(r.content) < 50000 or "The system can't perform the operation now. Try again later." == server_error:
            print("1" + str(len(r.content) < 50000))
            print("2" + str("The system can't perform the operation now. Try again later." == server_error))
            print("Get error with: https://scholar.google.com/scholar?start={}&q={}&hl=en&as_sdt=0,22".format(i, self.query))
            driver = webdriver.Chrome(seleniumwire_options=p)
            driver.get("https://scholar.google.com/scholar?start={}&q={}&hl=en&as_sdt=0,22".format(i, self.query))
            input()
            index = int(input("Proxy index: "))
            self.p, self.h = single_proxy_and_header(self.view_html, index)
            soup = None
            # if not self.single_proxy == 0:
                # self.proxy_and_headers.drop(str(p))
                # print(len(self.proxy_and_headers.columns))
                # input(len(self.proxy_and_headers.columns) == 0)
                # if len(self.proxy_and_headers.columns):
                    # print("Your proxy is empty now! Please refresh it mannually!")
                    # if os.path.exists(self.proxy_and_headers_file):
                    #     shutil.rmtree(self.proxy_and_headers_file)
                    # input()
                    # # After you refresh your proxy and headers. We get a new one
                    # self.proxy_and_headers = get_proxy_and_headers(self.proxy_and_headers_file)
                    # soup = None
        
        return soup

    def _get_maximun_limitation_of_aritlces(self, soup):
        # Get maximum num of articles I can get
        limit_num = str(soup.findAll("div", {"class": "gs_ab_mdw"})[1])
        start = limit_num.index("About")
        end = limit_num.index("results")
        
        if ',' in limit_num[start+6 : end-1]:
            limit_num = int(limit_num[start+6 : end-1].replace(",", ""))
        elif '.' in limit_num[start+6 : end-1]:
            limit_num = int(limit_num[start+6 : end-1].split('.')[0])
        else:
            print(limit_num)
        print("You can have at most {} articles".format(limit_num))
        return limit_num

    def _download_articles_based_on_search(self, soup, i, articles):
        # Go over all articles I get in one turn google search
        for result in soup.findAll("div", {"class": "gs_r gs_or gs_scl"}):
            links = []
            title = None
            num_articles = len(articles)

            # Get one article title and all links
            for link in result.findAll('a', href=re.compile("http")):
                if title == None:
                    title = "".join([content.text for content in link.contents])
                elif len("".join([content.text for content in link.contents])) > len(title):
                    title = "".join([content.text for content in link.contents])
                links.append(link['href'])
            # Try to get the pdf and text file

            success_download_num = len(articles)+self.downloaded

            for link in links:
                if self.verbose:
                    print("Downloading article: %s" % title)
                    print("{} | Getting ariticles {}({}) {:.2f}% | {}".format(i, success_download_num, self.inquire_num, 100*(success_download_num)/self.inquire_num, link))
                if self._download_single_pdf(title, link):
                    articles.append({"title": title,"link":link})
                    break

            if not self.verbose:
                if len(articles) > num_articles:
                    print("{} | Get ariticles {}({}) {:.2f}% | {}".format(i, success_download_num, self.inquire_num, 100*success_download_num/self.inquire_num,  articles[-1]['link']))
                else:
                    print("{} | Article not found: {}".format(i, title))

    def _download_articles(self):
        articles = []
        limit_num = 0

        # loop to download pdf link
        i = self.start
        while True:
            if i != self.start and i > limit_num:
                # No more articles to get
                print("No more articles to get!")
                break
            if len(articles) > self.inquire_num:
                # I get enough articles
                print("Get enough articles!")
                break

            p, h = self._set_up_proxy_and_header(i)
            soup = self._search_article_names_from_google(i, p, h)
            if soup is None:
                continue
            if limit_num == self.start:
                limit_num = self._get_maximun_limitation_of_aritlces(soup)
            self._download_articles_based_on_search(soup, i, articles)
            i += 10

    def download_articles(self, inquire_num, query, start=0, downloaded=0) -> None:
        """
        Args:
            num (int): The number of articles you want to download.
            query (str): The query you use on google scholar search.
            download_path (str): The name of folder you want to save. It removes the origin folder and create a new one to save download data (ie: 'download').

        Returns:
            articles (list): A list of dictionary object which contains the articles' title and their source url. like:
                [{title: str, links: str}, ...]
        """
        
        self.inquire_num = inquire_num
        self.query = query
        self.start = start
        self.downloaded = downloaded
        
        if start == 0:
            self.save_path = self._recreate_save_folder()
        
        # Get the proxy and headers
        # self.proxy_and_headers = get_proxy_and_headers(self.proxy_and_headers_file)
        
        # Download articles
        self._download_articles()

if __name__ == '__main__':
    # # set up
    # s = scrap()
    # s.set_verbose(True)
    # p, h = s._set_up_proxy_and_header()
    # s.query = 'monosaccharides'
    # s.inquire_num = 100000

    # # # test google search
    # for i in range(90, 100, 10):
    #     soup = s._search_article_names_from_google(i, p, h)
    #     s._download_articles_based_on_search(soup, i, [])


    # test maximun number of articles

    # with open('../log/view.html', 'r', encoding='utf-8') as f:
    #     soup = BeautifulSoup(f.read(), 'html.parser')
    # scrap._get_maximun_limitation_of_aritlces(None, soup)    

    f = open('../log/view.html', 'r', encoding='utf-8')
    soup = BeautifulSoup(f.read(), 'html.parser')
    print(soup.body.h1.contents[0])
    # File not found error
