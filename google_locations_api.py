import requests
import json

def get_location_name(sentence: str):
    """
        Function using MapQuest GeoEncoding API to get city name/ lat/ long

        Args:
            sentence: String
        
        Returns:
            Top City Name from the sentence
    """
    endpoint = 'http://www.mapquestapi.com/geocoding/v1/address'
    key = 'dSjSvjh2E3UH50JFVapQGxDhZWmPadQp' 
    # key = 'nGkXviL8M8Hc3Mp0trCbqJgB3jHRERpe' 
    params = {
        'key': key,
        'location': sentence,
        'outFormat': 'json'
    }

    response = requests.get(endpoint, params=params)
    data = json.loads(response.text)
    locations = data['results'][0]['locations']
    # place_names = [loc["adminArea5"] for loc in locations]
    lat_lang = [loc["latLng"] for loc in locations]
    return lat_lang[0]

if __name__ == "__main__":
    print(get_location_name("Bangalore"))