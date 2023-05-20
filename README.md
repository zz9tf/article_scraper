# Article scraper: Downloading acadimic articles with special topic

The Article Scraper is a Python script designed to facilitate the automated downloading of academic articles with a specific topic based on **[Elsevier Research API](https://dev.elsevier.com/)**. This tool can be particularly useful for researchers, students, or anyone who needs to gather a collection of scholarly articles on a particular subject. By using this scraper, you can save time and effort by automating the article retrieval process.

PS: Your university/institution has to have right to use **Elsevier Research API**, you need to use your own Elsevier Research API key to use this script.

## Features

- **Topic-based Article Search**: The scraper allows you to search for articles based on a specific topic or keyword. This helps you narrow down your search and retrieve articles relevant to your research interest.

- **PDF Download**: The script automatically downloads the articles in PDF format, making it easier for you to store, read, and analyze the content offline.

## Prerequisites

Before using the Article Scraper, ensure that you have the following prerequisites installed and prepared:

- [Elsevier Research API key](https://dev.elsevier.com/)
- Python 3.x installed
- Required Python packages (listed in requirements.txt)

## Installation

1. Clone the repository or download the script to your local machine.

```
git clone https://github.com/zz9tf/article_scraper.git
```

2. Open a terminal or command prompt and navigate to the project directory.
```
cd repository
```

3. Create .env file at root folder:
```
# scraper.py
scopus_api_key=<your Elsevier Research api key>
```

4. To install the necessary Python packages, run the following command:

```
# Setup environment
conda create --name art_scr python=3.11
conda activate art_scr

# Install packages
pip install -r requirements.txt
```

## Usage

Run the following command to execute the scraper:
```
python article_scraper.py --num <number_of_articles> --query <search_query> --start <start_index> --downloaded <num_downloaded> --cursor --csv_only --results <results_csv_file> --restart --prefix <prefix_number>
```

The available command-line arguments are as follows:

--num: The number of articles to download.
--query: The query used on Google Scholar search.
--start: The starting index of articles to download.
--downloaded: The number of articles already downloaded.
--cursor: Limit the use of '*' in the API.
--csv_only: Download only the CSV file from the API.
--results: Load results.csv locally downloaded from Scopus.
--restart: Restart the download process based on the previous index and downloaded articles.
--prefix: Start a customer prefix mode (1 or 2 or any customer prefix mode you set in main.py).

PS: You need to use your institution's direct IP network for this script, because Elsevier Research API will only be authenticated if you use it while within the network of your university/institution.

## Examples
Here are a few examples of how to use the Article Scraper:

1. Download articles using the Scopus API:
```
python article_scraper.py --num 10000 --query "your_topic_here"
```

2. Download only articles meta info from the Scopus API and save as a CSV file:
```
python article_scraper.py --num 10000 --query "your_topic_here" --csv_only
```

3. Download articles based on a locally downloaded results.csv file:
```
python article_scraper.py --results results.csv --restart
```

4. Start a custom prefix mode (You can setup your own custom prefix pipeline):
```
python article_scraper.py --prefix <your custom number>
```

## Limitations

- The scraper relies on available Scopus databases and repositories. It may not cover all sources, and access to certain articles may require a subscription or authentication.

- The script fetches articles based on the available metadata and search capabilities of the data sources. The search results may vary depending on the source and the specificity of the topic.

- The scraper is designed for academic articles and may not work optimally for other types of publications or websites.

## Contributing

Contributions to the Article Scraper are welcome! If you find any issues or have suggestions for improvements, please submit an issue or a pull request on the project repository.

## License

The Article Scraper is released under the [MIT License](LICENSE). Feel free to modify and distribute the script according to the terms of the license.

## Disclaimer

The Article Scraper is intended for personal use and academic research purposes only. Make sure to respect copyright laws and the terms of service of the data sources when using the tool. The developers are not responsible for any misuse or legal issues arising from the use of this scraper.
