from utils import read_env, helper_function
import re
import os
import pandas as pd
import json
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import PyPDF2
import shutil
import string

class scrap:
    def __init__(self, scopus_api_key, verbose=False) -> None:
        
        self.scopus_api_key = scopus_api_key
        
        # Create folders
        self.root = Path(__file__).parent.parent
        self.save_folder = os.path.join(self.root, 'download')
        self.log_folder = os.path.join(self.root, 'log')
        if not os.path.exists(self.log_folder):
            os.mkdir(self.log_folder)

        self.view_html = os.path.join(self.log_folder, 'view.html')
        self.verbose = verbose
        self.sep = os.path.sep

    def set_verbose(self, verbose):
        if type(verbose) is bool:
            self.verbose = verbose
        else:
            raise ValueError("Expected boolean value, got %s" % verbose)

    def download_articles(self, inquire_num, query, start=0, downloaded=0, cursor=False) -> None:
        """
        Args:
            num (int): The number of articles you want to download.
            query (str): The query you use on google scholar search.
            start (int): The index of articles you want to download.(ie: you want to start the index at where
                you stoped last time). Defualt value is 0.
            downloaded (int): The number of articles you have sucessfully downloaded. It's for calculate how much articles
                you still need to download(ie: inquire_num - downloaded = articles_you_still_need)
            cursor (bool): If you are limited for using '*' in api.
        """
        
        self.inquire_num = inquire_num
        self.query = query
        self.start = start
        self.downloaded = downloaded
        self.cursor = '*' if cursor else None  # limit number 5000 if cursor is None
        
        if start == 0:
            self.save_path = self._recreate_save_folder()
 
        # Download articles
        return self._download_articles()

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

    def _download_articles(self):
        articles = []
        scopus_results = []
        limit_num = 5000 if self.cursor is None else 0
        count_num = 25
        # loop to download pdf link
        i = self.start
        while True:
            if i != self.start and i >= limit_num:
                # No more articles to get
                print("No more articles to get!")
                break
            if len(articles) > self.inquire_num:
                # I get enough articles
                print("Get enough articles!")
                break

            js = self._search_article_names_from_scopus(i)
            entries = js['search-results']['entry']
            scopus_results += [s._parse_article(entry) for entry in entries]
            pd.DataFrame(scopus_results).to_csv(os.path.join(self.log_folder, 'result.csv'))
            
            if js is None:
                input("Something wrong with search article")
                
            if limit_num == self.start:
                limit_num = self._get_maximun_limitation_of_aritlces(js)
                
            self._download_articles_based_on_search(js, i, articles)
            i += count_num

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
                'httpAccept': 'application/json', 'view': 'STANDARD', 
                }
        else:
            par = {'apikey': self.scopus_api_key, 'query': self.query, 'start': index, "cursor": self.cursor, 
                'httpAccept': 'application/json', 'view': 'STANDARD', 
                }
        r = requests.get("https://api.elsevier.com/content/search/scopus", params=par)
        
        self.remain_usage = r.headers['X-RateLimit-Remaining']
        
        js = r.json()
        with open(self.view_html, "w") as outfile:
            outfile.write(json.dumps(js, indent=4))
        
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
                if link['@ref'] == 'scopus':
                    scopus_link = link['@href']
        except:
            scopus_link = None
            
        return pd.Series({'scopus_id': scopus_id, 'title': title, 'publication_name':publicationname,\
            'issn': issn, 'isbn': isbn, 'eissn': eissn, 'volume': volume, 'page_range': pagerange,\
            'cover_date': coverdate, 'doi': doi,'citation_count': citationcount, 'affiliation': affiliation,\
            'aggregation_type': aggregationtype, 'subtype_description': sub_dc, 'authors': author_id_list,\
            'scopus': scopus_link})

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
        results = pd.DataFrame([s._parse_article(entry) for entry in entries])
        
        # Go over all articles I get in one turn google search
        for i, row in results[['title', 'doi', 'scopus']].iterrows():
            title = row['title']
            
            num_articles = len(articles)
            success_download_num = len(articles)+self.downloaded
            
            if self.verbose:
                print("Downloading article: %s" % title)
                print("{} | Getting ariticles {}({}) {:.2f}% | {}".format(i, success_download_num, self.inquire_num, 100*(success_download_num)/self.inquire_num))
            if self._download_single_pdf(title):
                articles.append(title)
                break

            if not self.verbose:
                if len(articles) > num_articles:
                    print("{} | Downloaded ariticles {}({}) {:.2f}% | {}".format(i, success_download_num, self.inquire_num, 100*success_download_num/self.inquire_num,  articles[-1]))
                else:
                    print("{} | Article not found: {}".format(i, title))

    def _download_single_pdf(self, title):
        # Get link from google scholar
        params = {
            'hl': 'en',
            'q': title,
            'as_sdt': '0,22',
            'btnG': ''
        }
        url = "https://scholar.google.com/scholar"
        r = requests.get(url, params)
        print(r.url)
        with open(self.view_html, 'wb') as f:
            f.write(r.content)
        
        
        return True
    
    def _remove_between_tags(self, string):
        pattern = r"<[^>]+>"
        result = re.sub(pattern, "", string)
        return result

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



if __name__ == '__main__':
    # # set up
    s = scrap(os.getenv('scopus_api_key'))
    s.set_verbose(True)
    df = pd.read_csv('result.csv')
    for row in df['title']:
        title = s._remove_between_tags(row)
        s._download_single_pdf(title)
        time.sleep(1)