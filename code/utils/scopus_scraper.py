import requests
import json
import pandas as pd
        
def search_scopus(apikey, query, view, index=0, cursor=None, view_html='view.html'):
    '''
        Search Scopus database using key as api key, with query.
        Search author or articles depending on type_

        Parameters
        ----------
        key : string
            Elsevier api key. Get it here: https://dev.elsevier.com/index.html
        query : string
            Search query. See more details here: http://api.elsevier.com/documentation/search/SCOPUSSearchTips.htm
        type_ : string or int
            Search type: article or author. Can also be 1 for article, 2 for author.
        view : string
            Returned result view (i.e., return fields). Can only be STANDARD for author search.
        index : int
            Start index. Will be used in search_scopus_plus function

        Returns
        -------
        pandas DataFrame
    '''
    if cursor is None:
        par = {'apikey': apikey, 'query': query, 'start': index,
            'httpAccept': 'application/json', 'view': view, 
            }
    else:
        
        par = {'apikey': apikey, 'query': query, 'start': index, "cursor": cursor, 
            'httpAccept': 'application/json', 'view': view, 
            }
    r = requests.get("https://api.elsevier.com/content/search/scopus", params=par)
    js = r.json()
    with open(view_html, "w") as outfile:
        outfile.write(json.dumps(js, indent=4))
    
    if 'service-error' in js.keys():
        # No articles founded
        return None
    
    total_count = int(js['search-results']['opensearch:totalResults'])
    print("Found articles: {}".format(total_count))
    
    entries = js['search-results']['entry']

    result_df = pd.DataFrame([_parse_article(entry) for entry in entries])
    
    if cursor is None:
        return result_df
    
    return result_df, cursor
    
def _parse_article(entry):
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
        affiliation = _parse_affiliation(entry['affiliation'])
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
        full_text_link = None
        for link in link_list:
            if link['@ref'] == 'full-text':
                full_text_link = link['@href']
    except:
        full_text_link = None

    return pd.Series({'scopus_id': scopus_id, 'title': title, 'publication_name':publicationname,\
            'issn': issn, 'isbn': isbn, 'eissn': eissn, 'volume': volume, 'page_range': pagerange,\
            'cover_date': coverdate, 'doi': doi,'citation_count': citationcount, 'affiliation': affiliation,\
            'aggregation_type': aggregationtype, 'subtype_description': sub_dc, 'authors': author_id_list,\
            'full_text': full_text_link})

def _parse_affiliation(js_affiliation):
    l = list()
    for js_affil in js_affiliation:
        name = js_affil['affilname']
        city = js_affil['affiliation-city']
        country = js_affil['affiliation-country']
        l.append({'name': name, 'city': city, 'country': country})
    return l

