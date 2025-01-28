import pandas as pd
import requests
import logging
from bs4 import BeautifulSoup
from io import StringIO
from urllib.request import Request, urlopen
from datetime import datetime
url = "https://en.wikipedia.org/wiki/Star_Wars"

''' 
requests.raise_for_status -> needs for checking the status codes 

Exceptions are needed for requests:

In the event of a network problem (e.g. DNS failure, refused connection, etc), 
Requests will raise a ConnectionError exception.

In the event of the rare invalid HTTP response, Requests will raise an HTTPError exception.

If a request times out, a Timeout exception is raised.

If a request exceeds the configured number of maximum redirections, a TooManyRedirects exception is raised.

All exceptions that Requests explicitly raises inherit from requests.exceptions.RequestException.

We could have either more detailed approach for exception handling or add only the RequestException to handle all cases.
'''

def scrape_website_requests(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    
    except  requests.exceptions.HTTPError as http_error:
        logging.error(f"HTTP Error: {http_error.args[0]}")
    
    except requests.exceptions.ConnectionError as con_error:
        logging.error(f"Connection Error: {con_error.args[0]}")
       
    except requests.exceptions.Timeout as time_error:
        logging.error(f"Timeout Error: {time_error.args[0]}")
    
    except requests.exceptions.TooManyRedirects as red_error:
        logging.error(f"TooManyRedirects Error: {red_error.args[0]}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Request Exception Error: {e.args[0]}")
        raise  SystemExit(con_error)

''' Question: to use response.text or response.content
The .content is better to use as it holds raw bytes, 
and can decode better then the text representation of the .text
'''
def extract_data(url):
    response = scrape_website_requests(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_='wikitable plainrowheaders')
    df = pd.read_html(StringIO(str(table)), header = 0)[0] # needed for the multilines headers
    # df = pd.concat(df)
    df.to_csv("star_wars.csv", index = False)
    return df

def process_skywalker_films(df):
    df = extract_data(url)
    df["Trilogy"] = None

    trilogy = ""
    for index, row in df.iterrows():

        if "trilogy" in row["Film"]:
            trilogy = row["Film"]
        else:
                df.at[index,'Trilogy'] = trilogy ## Iterrows are just a copy, they just 
        
    df = df[~df["Film"].str.contains("trilogy")]

    #Change the date format
    date_format = '%m %d, %Y'
    df["U.S. release date"] = pd.to_datetime(df["U.S. release date"])

    # remove unnecessary columns
    df.drop(['Refs.', 'Unnamed: 7'], axis=1, inplace=True)
    return df
    # pd.set_option("display.max_columns", None)

    #check the null values
    #print(df.isna().sum()) ## No null values -> perfect

#Next Steps: Download the rest of the tables + create a function
# Documentation: https://www.educative.io/answers/how-to-find-elements-by-class-using-beautiful-soup 
def extract_standalone_films(url):
    
    response = scrape_website_requests(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.select("table[class*='wikitable plainrowheaders']")[1]

    df = pd.read_html(StringIO(str(table)), header = 0)[0] # needed for the multilines headers
    # df = pd.concat(df)
    df.to_csv("star_wars.csv", index = False)
    return df


# print(extract_standalone_films(url))

def extract_upcoming_movies(url):
    response = scrape_website_requests(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.select("table[class*='wikitable plainrowheaders']")[2]
    df = pd.read_html(StringIO(str(table)), header = 0)[0] # needed for the multilines headers
    # df = pd.concat(df)
    df.to_csv("star_wars.csv", index = False)
    return df

#print(extract_upcoming_movies(url)) # Difference in the Status
def extract_television_series(url):
    response = scrape_website_requests(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.select("table[class*='wikitable plainrowheaders']")[3]
    df = pd.read_html(StringIO(str(table)), header = 0)[0] # needed for the multilines headers
    # df = pd.concat(df)
    df.to_csv("star_wars.csv", index = False)
    return df

# print(extract_television_series(url))

def extract_special_films(url):
    response = scrape_website_requests(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.select("table[class*='wikitable plainrowheaders']")[4]
    df = pd.read_html(StringIO(str(table)), header = 0)[0] # needed for the multilines headers
    # df = pd.concat(df)
    df.to_csv("star_wars.csv", index = False)
    return df

# print(extract_special_films(url))

def extract_films(url, index):
    
    response = scrape_website_requests(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.select("table[class*='wikitable plainrowheaders']")[index]

    df = pd.read_html(StringIO(str(table)), header = 0)[0] # needed for the multilines headers
    # df = pd.concat(df)
    df.to_csv("star_wars.csv", index = False)
    return df

#Extract several tables
skywalker_films = extract_films(url, 0)
skywalker_films = process_skywalker_films(skywalker_films)
standalone_films = extract_films(url, 1)
upcoming_films = extract_films(url, 2)
tv_series = extract_films(url, 3) # has the same multi-index lines
special_films = extract_films(url, 4)
print(special_films)

# Process the tables separately + write functions with repetitive code
# Make a function to combine all tables after scraping