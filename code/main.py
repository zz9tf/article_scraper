import os
from utils import read_env
from scraper import scrap

key = os.getenv('scopus_api_key')
s = scrap(key)
# s.set_verbose(True)
s.download_articles(10000, "", results="monosaccharides.csv")
print("Done!")