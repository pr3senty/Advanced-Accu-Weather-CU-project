import pandas as pd
from enum_classes import TimeRange


METRICS = [
    "Temperature",
    "WindSpeed",
    "PrecipitationProbability",
    "ThunderstormProbability"
]

def rate_forecast_by_metrics(df: pd.DataFrame, include_dataframe=True) -> dict:
    mean_temperature = int(df["Temperature"].mean())
    mean_wind_speed = int(df["WindSpeed"].mean())
    mean_precipitation_probability = int(df["PrecipitationProbability"].mean())
    mean_thunderstorm_probability = int(df["ThunderstormProbability"].mean())
    df["DateTime"] = pd.to_datetime(df["DateTime"])

    analysis_result = {
        "rate": "good",
        "dataframe": df.copy() if include_dataframe else "",
        "mean_temperature":
            {
                "value": mean_temperature,
                "rate": "good"
            },
        "mean_wind_speed":
            {
                "value": mean_wind_speed,
                "rate": "good"
            },
        "mean_precipitation_probability":
            {
                "value": mean_precipitation_probability,
                "rate": "good"
            },
        "mean_thunderstorm_probability":
            {
                "value": mean_thunderstorm_probability,
                "rate": "good"
            },
    }

    flag = False

    if mean_temperature > 30 or mean_temperature < -20:
        analysis_result["mean_temperature"]["rate"] = "bad"
        flag = True

    if mean_wind_speed > 50:
        analysis_result["mean_wind_speed"]["rate"] = "bad"
        flag = True

    if mean_precipitation_probability > 85:
        analysis_result["mean_precipitation_probability"]["rate"] = "bad"

    if mean_thunderstorm_probability > 75:
        analysis_result["mean_thunderstorm_probability"]["rate"] = "bad"
        flag = True

    if flag:
        analysis_result["rate"] = "bad"

    return analysis_result

def analyze_forecast(forecast_data: dict, time_range : TimeRange, include_dataframe=True) -> dict:
    if time_range == TimeRange.HOURS12:
        return analyze_hourly_forecast(forecast_data, include_dataframe)

    if time_range == TimeRange.DAYS5:
        return analyze_daily_forecast(forecast_data, include_dataframe)

def analyze_hourly_forecast(data : dict, include_dataframe=True):
    df = pd.DataFrame(columns=[
        "Temperature",
        "WindSpeed",
        "PrecipitationProbability",
        "ThunderstormProbability",
        "DateTime"
    ])


    for hour in data:
        datetime = hour["DateTime"].split("+")[0]

        temperature = hour["Temperature"]["Value"]
        wind_speed = hour["Wind"]["Speed"]["Value"]
        wind_direction = hour["Wind"]["Direction"]["Localized"]
        precipitation_probability = hour["PrecipitationProbability"]
        thunderstorm_probability = hour["ThunderstormProbability"]

        df.loc[len(df.index)] = [temperature, wind_speed, precipitation_probability, thunderstorm_probability, datetime]


    return rate_forecast_by_metrics(df, include_dataframe)

def analyze_daily_forecast(data: dict, include_dataframe=True):
    data = data["DailyForecasts"]

    df = pd.DataFrame(columns=[
        "Temperature",
        "WindSpeed",
        "PrecipitationProbability",
        "ThunderstormProbability",
        "DateTime"
    ])

    for day in data:

        datetime = day["Date"].split("+")[0]
        temperature = (day["Temperature"]["Minimum"]["Value"] + day["Temperature"]["Maximum"]["Value"]) / 2
        wind_speed = (day["Day"]["Wind"]["Speed"]["Value"] + day["Night"]["Wind"]["Speed"]["Value"]) / 2
        wind_direction = day["Day"]["Wind"]["Direction"]["Localized"]
        precipitation_probability = (day["Day"]["PrecipitationProbability"] + day["Night"]["PrecipitationProbability"]) / 2
        thunderstorm_probability = (day["Day"]["ThunderstormProbability"] + day["Night"]["ThunderstormProbability"]) / 2

        df.loc[len(df.index)] = [
            temperature,
            wind_speed,
            precipitation_probability,
            thunderstorm_probability,
            datetime
        ]

    return rate_forecast_by_metrics(df, include_dataframe)

def get_custom_forecast(
    temperature,
    wind_speed,
    thunderstorm_probability,
    precipitation_probability
):
    df = pd.DataFrame({
        "Temperature": [temperature],
        "WindSpeed": [wind_speed],
        "PrecipitationProbability": [precipitation_probability],
        "ThunderstormProbability": [thunderstorm_probability]
    })

    return rate_forecast_by_metrics(df)
