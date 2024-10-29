from flask import Flask, render_template, request
from logic import get_suitable_cities
from rate_forecast import analyze_forecast, get_custom_forecast
from api_requests import get_forecast, RequestsExceeded
from enum_classes import TimeRange, Result
import json


apikey = ""
app = Flask(__name__)
cities = {}
cities_name = {}

time_ranges = {
    "12 часов": TimeRange.HOURS12,
    "5 дней": TimeRange.DAYS5,
}


@app.get("/")
def index_get():
    return render_template("form.html", time_ranges=time_ranges.keys())

@app.post("/")
def index_post():
        start_point = request.form["start_point"].lstrip(" ").rstrip(" ")
        end_point = request.form["end_point"].lstrip(" ").rstrip(" ")
        time_range = request.form["time_range"].lstrip(" ").rstrip(" ")

        # check empty values
        if len(start_point) == 0 or len(end_point) == 0 or len(time_range) == 0:

            return show_result(
                Result.EMPTY_FIELDS,
                start_point=start_point,
                end_point=end_point,
                time_range=time_range
            )

        suitable_cities_for_start = get_suitable_cities(start_point, cities_name)
        suitable_cities_for_end = get_suitable_cities(end_point, cities_name)

        match_start_city = suitable_cities_for_start["match"]
        match_end_city = suitable_cities_for_end["match"]

        # check incorrect input
        if any([
            time_range not in time_ranges.keys(),
            not match_start_city,
            not match_end_city
        ]):
            start_cities = list(suitable_cities_for_start.keys())[1:]
            end_cities = list(suitable_cities_for_end.keys())[1:]
            
            return show_result(
                Result.INCORRECT_INPUT,
                match_start_city=match_start_city,
                match_end_city=match_end_city,
                start_cities=start_cities[:min(5, len(start_cities))],
                end_cities=end_cities[:min(5, len(end_cities))],
                start_point=(start_point if match_start_city else ""),
                end_point=(end_point if match_end_city else ""),
                time_range=time_range,
            )

        # do weather analysis
        start_city, end_city, time_range = list(suitable_cities_for_start.items())[1], \
        list(suitable_cities_for_end.items())[1], time_ranges[time_range]

        try:
            s_forecast = get_forecast(start_city[1], cities[start_city[1]], time_range, apikey)
            e_forecast = get_forecast(end_city[1], cities[end_city[1]], time_range, apikey)
        except RequestsExceeded:
            return show_result(Result.ERRORS, errors=["The allowed number of requests has been exceeded."])

        analyzed_s_forecast = analyze_forecast(s_forecast, time_range)
        analyzed_e_forecast = analyze_forecast(e_forecast, time_range)

        forecast_rate = "bad" if (analyzed_s_forecast["rate"] == "bad" or analyzed_e_forecast["rate"] == "bad") else "good"

        return show_result(
            Result.SUCCESSFUL,
            forecast_rate=forecast_rate,
            s_forecast=analyzed_s_forecast,
            e_forecast=analyzed_e_forecast,
            start_city=start_city[0],
            end_city=end_city[0]
        )


def show_result(result : Result, **kwargs):
    if result == Result.INCORRECT_INPUT:
        start_cities = kwargs["start_cities"]
        end_cities = kwargs["end_cities"]

        match_start_city = kwargs["match_start_city"]
        match_end_city = kwargs["match_end_city"]
        start_point = kwargs["start_point"] if match_start_city else ""
        end_point = kwargs["end_point"] if match_end_city else ""
        time_range = kwargs["time_range"] if "time_range" in kwargs else ""
        incorrect_time_range = time_range not in time_ranges.keys()

        return render_template(
            "show_incorrect_input.html",
            match_start_city=match_start_city,
            match_end_city=match_end_city,
            start_cities=start_cities,
            end_cities=end_cities,
            start_point=start_point,
            end_point=end_point,
            time_ranges=time_ranges.keys(),
            time_range=("" if incorrect_time_range else time_range),
            incorrect_time_range=incorrect_time_range
        )

    if result == Result.EMPTY_FIELDS:
        start_point = kwargs["start_point"]
        end_point = kwargs["end_point"]
        time_range = kwargs["time_range"]

        return render_template(
            "show_empty_fields.html",
            start_point=start_point,
            end_point=end_point,
            time_range=time_range,
            time_ranges=time_ranges.keys()
        )

    if result == Result.SUCCESSFUL:
        forecast_rate = kwargs["forecast_rate"]
        s_forecast = kwargs["s_forecast"]
        e_forecast = kwargs["e_forecast"]
        start_city = kwargs["start_city"]
        end_city = kwargs["end_city"]

        return render_template(
            "show_successful.html",
            forecast_rate=forecast_rate,
            start_city=start_city,
            s_temperature_rate=s_forecast["mean_temperature"]["rate"],
            s_temperature=s_forecast["mean_temperature"]["value"],
            s_wind_speed_rate=s_forecast["mean_wind_speed"]["rate"],
            s_wind_speed=s_forecast["mean_wind_speed"]["value"],
            s_precipitation_probability_rate=s_forecast["mean_precipitation_probability"]["rate"],
            s_precipitation_probability=s_forecast["mean_precipitation_probability"]["value"],
            s_thunderstorm_probability_rate=s_forecast["mean_thunderstorm_probability"]["rate"],
            s_thunderstorm_probability=s_forecast["mean_thunderstorm_probability"]["value"],
            end_city=end_city,
            e_temperature_rate=e_forecast["mean_temperature"]["rate"],
            e_temperature=e_forecast["mean_temperature"]["value"],
            e_wind_speed_rate=e_forecast["mean_wind_speed"]["rate"],
            e_wind_speed=e_forecast["mean_wind_speed"]["value"],
            e_precipitation_probability_rate=e_forecast["mean_precipitation_probability"]["rate"],
            e_precipitation_probability=e_forecast["mean_precipitation_probability"]["value"],
            e_thunderstorm_probability_rate=e_forecast["mean_thunderstorm_probability"]["rate"],
            e_thunderstorm_probability=e_forecast["mean_thunderstorm_probability"]["value"],
            time_ranges=time_ranges.keys(),
        )

    if result == Result.ERRORS:
        errors = kwargs["errors"]

        return render_template("show_error.html", errors=errors)

if __name__ == "__main__":

    # load api key
    with open("app.properties") as file:
        apikey = file.readline().split("=")[1]

        assert(apikey != "")

    # load cities
    with open("cities.json", encoding="utf-8") as file:
        cities = json.load(file)

        for uuid, info in cities.items():
            ru_name, en_name = info["translated_city_names"].values()

            cities_name[ru_name] = uuid
            cities_name[en_name] = uuid

    app.run()