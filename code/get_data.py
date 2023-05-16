import csv
import numpy as np
from scopus import search_scopus, retrieve_full_text

def download_articles(num=100):
    i = 0
    all_articles = []
    while True:
        # Get articles
        df = search_scopus(apikey=key, query="TITLE-ABS-KEY(oligosaccharide)", view="STANDARD", index=i)
        if df is None:
            break
        
        # Get all articles which I can donwload
        df = df[~df['full_text'].isna()].reset_index()
        
        for idx, row in df.iterrows():
                full_text = retrieve_full_text(apikey=key, full_text_link=row['full_text'])
                if full_text is not None:
                    all_articles.append({'title': row['title'], 'full_text': full_text})
                    
        print("Get ariticles {}({}) {:.2f}% | Searched articles: {}  ({})".format(
                len(all_articles), num, 100*len(all_articles)/num, 
                i+25, int((i+25)*num/len(all_articles))
            ))
        
        if len(all_articles) >= num:
            break
        i += 25
        
        csv_file = 'dataset.csv'
        with open(csv_file, 'w') as f:
            w = csv.DictWriter(f, all_articles[0].keys())
            w.writeheader()
            w.writerows(all_articles)
        
    print("\nFinished!")
    
    print("Saved as {}".format(csv_file))

download_articles(num=10000)