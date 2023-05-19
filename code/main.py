import os
from utils import read_env
from scraper import scrap

# Download csv file
# key = os.getenv('scopus_api_key')
# s = scrap(key)
# s.set_verbose(True)
# s.download_articles(20000, "monosaccharides", cursor=True, csv_only=True)

# Download PDF by local csv file
key = os.getenv('scopus_api_key')
s = scrap(key, True)
s.download_articles(results="result.csv", restart=True)

print("Done!")