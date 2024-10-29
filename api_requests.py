from enum_classes import TimeRange
import requests
import json


ACCU_WEATHER_FORECASTS_APIS = {
    TimeRange.HOURS12: "http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/",
    TimeRange.DAYS5: "http://dataservice.accuweather.com/forecasts/v1/daily/5day/",
}

cities_with_location_key = {}

class RequestsExceeded(Exception):
    pass

def get_location_area_key_for_city(city: dict, token: str) -> str:
    latitude, longitude = city["latitude"], city["longitude"]

    api_url = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"

    response = requests.request(
        "GET",
                api_url,
                params={
                    "apikey": token,
                    "q": f"{latitude}, {longitude}",
                }
    )

    if response.status_code == 503:
        raise RequestsExceeded("The allowed number of requests has been exceeded.")

    return json.loads(response.text)["Key"]


def get_forecast(city_uuid, city: dict, time_range : TimeRange, token: str) -> dict:

    if city_uuid in cities_with_location_key:
        city_location_key = cities_with_location_key[city_uuid]
    else:
        city_location_key = get_location_area_key_for_city(city, token)
        cities_with_location_key[city_uuid] = city_location_key


    response = requests.request(
        "GET",
        ACCU_WEATHER_FORECASTS_APIS[time_range] + city_location_key,
        params={
            "apikey": token,
            "language": "ru",
            "details": "true",
            "metric": "true"
        }
    )

    if response.status_code == 503:
        raise RequestsExceeded("The allowed number of requests has been exceeded.")

    return json.loads(response.text)