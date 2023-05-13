import os
from utils import read_env
from scraper import scrap

s = scrap()
s.download_articles(10000, "monosaccharides")
print("Done!")