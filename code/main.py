import os
from utils import read_env
from scraper import scrap
import argparse

def usage():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Article Scraper: Downloading Academic Articles with Special Topic")

    # Add argument for the number of articles to download
    parser.add_argument("--num", type=int, default=None, help="The number of articles to download")

    # Add argument for the query used on Google Scholar search
    parser.add_argument("--query", type=str, default=None, help="The query used on Google Scholar search")

    # Add argument for the starting index of articles to download
    parser.add_argument("--start", type=int, default=None, help="The starting index of articles to download")

    # Add argument for the number of articles already downloaded
    parser.add_argument("--downloaded", type=int, default=None, help="The number of articles already downloaded")

    # Add argument for limiting the use of '*' in the API
    parser.add_argument("--cursor", action="store_true", help="Limit the use of '*' in the API")

    # Add argument for downloading only the CSV file from the API
    parser.add_argument("--csv_only", action="store_true", help="Download only the CSV file from the API")

    # Add argument for loading results.csv locally downloaded from Scopus
    parser.add_argument("--results", type=str, default=None, help="Load results.csv locally downloaded from Scopus")

    # Add argument for restarting the download process based on previous index and downloaded articles
    parser.add_argument("--restart", action="store_true", help="Restart the download process")

    parser.add_argument("--prefix", action=int, default=None, help="Start a customer prefix mode")

    # Parse the arguments
    args = parser.parse_args()

    # Retrieve the values from the arguments
    num = args.num
    query = args.query
    start = args.start
    downloaded = args.downloaded
    cursor = args.cursor
    csv_only = args.csv_only
    results = args.results
    restart = args.restart
    prefix = args.prefix

    if perfix is None:
        # Call the article scraper function with the provided topic and output directory
        key = os.getenv('scopus_api_key')
        s = scrap(key, True)
        # Call the article scraper function with the provided arguments
        s.download_articles(
            inquire_num=num,
            query=query,
            start=start,
            downloaded=downloaded,
            cursor=cursor,
            csv_only=csv_only,
            results=results,
            restart=restart
        )
    elif prefix == 1:
        # Download csv file
        key = os.getenv('scopus_api_key')
        s = scrap(key)
        s.set_verbose(True)
        s.download_articles(20000, "monosaccharides", cursor=True, csv_only=True)
        
    elif prefix == 2:
        # Download PDF by local csv file
        key = os.getenv('scopus_api_key')
        s = scrap(key, True)
        s.download_articles(results="result.csv", restart=True)
    
    else:
        raise Exception("These is not such prefix with --prefix {}".format(prefix))

usage()
print("Done!")