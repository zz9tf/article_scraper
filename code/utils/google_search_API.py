import os
from utils import read_env
from serpapi import GoogleSearch

params = {
  "engine": "google_scholar",
  "q": "monosaccharides",
  "hl": "en",
  "num": 20,
  "api_key": os.getenv("google_api_key")
}

search = GoogleSearch(params)
results = search.get_dict()
print(results)