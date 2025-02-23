import pandas as pd
import requests
import logging
from bs4 import BeautifulSoup
from io import StringIO
from datawrapper import Datawrapper
import os
from dotenv import load_dotenv


### Preparations #####
logging.basicConfig(level=logging.INFO)

# Constants
URL = "https://en.wikipedia.org/wiki/Star_Wars"

#Load environment variables
load_dotenv()  
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise EnvironmentError("API_KEY environment variable is not set.")

dw = Datawrapper(access_token=API_KEY)


def scrape_website_requests(url:str) -> requests.Response:
    """
    Scrapes a website using requests and returns the response.
    
    Args:
        url (str): The URL to scrape.
    
    Returns:
        requests.Response: The response object.
    
    Raises:
        requests.exceptions.RequestException: If any request-related error occurs.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        raise
    
####### Extracting the data #######

def extract_films(URL:str, table_index:int, class_name:str ) -> pd.DataFrame:
    """
    Extracts film data from a Wikipedia page containing film data.
    
    Args:
        url (str): The URL of the Wikipedia page.
        table_index (int): The index of the table to extract.
        class_name (str): The class name pattern to select the table.
    
    Returns:
        pd.DataFrame: A DataFrame containing the extracted film data.
    """
    response = scrape_website_requests(URL)
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.select(f"table[class*='{class_name}']")
    
    # Check if the table's index is not out of the range of the table
    if table_index >= len(tables):
        raise IndexError("Table index out of range.")
    
    table = tables[table_index]
    df = pd.read_html(StringIO(str(table)), header = 0)[0] # needed for the multilines headers
    return df

####### Cleaning the data #######
def transform_date(df:pd.DataFrame) -> pd.DataFrame:
    """
    Converts the 'U.S. release date' column to datetime.
    
    Args:
        df (pd.DataFrame): DataFrame with the 'U.S. release date' column.
    
    Returns:
        pd.DataFrame: DataFrame with the transformed date column.
    """

    df["U.S. release date"] = pd.to_datetime(df["U.S. release date"])
    return df

def process_films(df: pd.DataFrame, needed_flag: bool)-> pd.DataFrame:
    """
    Processes the film DataFrame and optionally adds a 'Trilogy' column 
    
    Args:
        df (pd.DataFrame): The original film DataFrame.
        needed_flag (bool): Flag to determine if 'Trilogy' processing is needed.
    
    Returns:
        pd.DataFrame: A cleaned DataFrame with selected columns.
    """
     
    df = df.copy()
 
    if needed_flag:
        df["Trilogy"] = None

        trilogy = ""
        for index, row in df.iterrows():

            if "trilogy" in row["Film"]:
                trilogy = row["Film"]
            else:
                    df.at[index,'Trilogy'] = trilogy 
            
        df = df[~df["Film"].str.contains("trilogy")]
        df["U.S. release date"] = pd.to_datetime(df["U.S. release date"])
    else:
        df["U.S. release date"] = pd.to_datetime(df["U.S. release date"])
    
    return df.iloc[:,0:2]

def prepare_dw_data(film_category:dict) -> pd.DataFrame:
    """
    Prepares the data for visualization by extracting and processing film data.
    
    Args:
        film_categories (dict): A dictionary mapping film category names to table indices.
    
    Returns:
        pd.DataFrame: Processed DataFrame ready for visualization.
    """
    film_data = {}
    for category, index in film_category.items():
        film_data[category] = extract_films(URL, index, 'wikitable plainrowheaders')

    skywalker_films = process_films(film_data["Skywalker Films"], True)
    standalone_films = process_films(film_data["Standalone Films"], False)
    special_films = process_films(film_data["Special Films"], False)
    df = pd.concat([skywalker_films, standalone_films, special_films])


    ##### Prep for the DW visualization ##########
    df["Year"] = df['U.S. release date'].dt.year
    df.sort_values(by = "Year", ascending=True, inplace=True)
    dw_data = df[["Film", "Year"]]

    logging.info(f"Data prepared for Datawrapper:\n{dw_data}")

    return dw_data 


####### DataWrapper #######

def create_dw_chart(dw_data:pd.DataFrame) -> str:
    """
    Creates a Datawrapper chart with the given data.
    
    Args:
        dw_data (pd.DataFrame): DataFrame with visualization data.
    
    Returns:
        str: The chart ID of the newly created chart.
    """
    new_chart = dw.create_chart(
        title="Movies Release Timeline",
        chart_type="d3-dot-plot" ,  
        data = dw_data
    )

    return new_chart.get("id")


def update_dw_chart(chart_id:str) -> str:
    """
    Updates the Datawrapper chart with additional metadata and description.
    
    Args:
        chart_id (str): The chart ID to update.
    """
        
    # Fetch chart details to get the existing title
    chart_details = dw.get_chart(chart_id)
    current_title = str(chart_details.get("title", "Movies Release Timeline"))  # Ensure title is a string

    # Define the source information
    source_name = "Wikipedia"
    source_url = URL

    # Correct way to update the chart
    dw.update_chart(
        chart_id=chart_id,
        title=current_title,  #  Required to prevent errors
        metadata={
            "visualize": {
                "axes": {
                    "labels": {
                        "bottom": "Release Date"  #  Ensure correct X-axis label
                    },
                    "bottom": {  
                        "scale": "time",  #  Treat the X-axis as a date
                        "custom-range": [str(2015), str(2017)],  #  Set exact range for X-axis
                        "custom-tick-format": "%Y"  #  Display only the year (YYYY)

                    }
                }
            }
        }
    )

    dw.update_description(chart_id=chart_id, source_name = source_name, source_url=source_url)
    logging.info(f"Chart updated: https://datawrapper.dwcdn.net/{chart_id}/")

def main():
    """
    Main function to prepare data, create a Datawrapper chart, and update it.
    
    Returns:
        str: Completion message.
    """
    film_category = {"Skywalker Films":0,
                    "Standalone Films": 1,
                    "Special Films": 4}
    dw_data = prepare_dw_data(film_category)
    chart_id = create_dw_chart(dw_data)
    update_dw_chart(chart_id)
    return "Done"

if __name__ == "__main__":
    print(main())
