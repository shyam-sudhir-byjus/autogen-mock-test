import requests
import json
from get_parameters import MAPQUEST_API_KEY

def get_location_name(sentence: str):
    """
        Function using MapQuest GeoEncoding API to get city name/ lat/ long

        Args:
            sentence: String
        
        Returns:
            Top City Name from the sentence
    """
    endpoint = 'http://www.mapquestapi.com/geocoding/v1/address'
    key = MAPQUEST_API_KEY
    # key = 'nGkXviL8M8Hc3Mp0trCbqJgB3jHRERpe' 
    params = {
        'key': key,
        'location': sentence,
        'outFormat': 'json'
    }

    response = requests.get(endpoint, params=params)
    data = json.loads(response.text)
    locations = data['results'][0]['locations']
    lat_lang = [loc["latLng"] for loc in locations]
    return lat_lang[0]

if __name__ == "__main__":
    print(get_location_name("Bangalore"))