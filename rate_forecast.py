from enum_classes import TimeRange


def rate_forecast_by_metrics(
    mean_temperature,
    mean_wind_speed,
    mean_thunderstorm_probability,
    mean_precipitation_probability,
) -> dict:
    analysis_result = {
        "rate": "good",
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
            }
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

def analyze_forecast(forecast_data: dict, time_range : TimeRange) -> dict:
    if time_range == TimeRange.HOURS12:
        return analyze_hourly_forecast(forecast_data)

    if time_range == TimeRange.DAYS5:
        return analyze_daily_forecast(forecast_data)

def analyze_hourly_forecast(data : dict):
    mean_temperature = 0
    mean_wind_speed = 0
    mean_thunderstorm_probability = 0
    mean_precipitation_probability = 0

    for hour in data:
        temperature = hour["Temperature"]["Value"]
        wind_speed = hour["Wind"]["Speed"]["Value"]
        wind_direction = hour["Wind"]["Direction"]["Localized"]
        precipitation_probability = hour["PrecipitationProbability"]
        thunderstorm_probability = hour["ThunderstormProbability"]

        mean_temperature += temperature
        mean_wind_speed += wind_speed
        mean_precipitation_probability += precipitation_probability
        mean_thunderstorm_probability += thunderstorm_probability

    mean_temperature //= len(data)
    mean_wind_speed //= len(data)
    mean_precipitation_probability //= len(data)
    mean_thunderstorm_probability //= len(data)

    return rate_forecast_by_metrics(
        mean_temperature,
        mean_wind_speed,
        mean_thunderstorm_probability,
        mean_precipitation_probability
    )

def analyze_daily_forecast(data: dict):
    data = data["DailyForecasts"]

    mean_temperature = 0
    mean_wind_speed = 0
    mean_thunderstorm_probability = 0
    mean_precipitation_probability = 0

    for day in data:
        temperature = (day["Temperature"]["Minimum"]["Value"] + day["Temperature"]["Maximum"]["Value"]) / 2
        wind_speed = (day["Day"]["Wind"]["Speed"]["Value"] + day["Night"]["Wind"]["Speed"]["Value"]) / 2
        wind_direction = day["Day"]["Wind"]["Direction"]["Localized"]
        precipitation_probability = (day["Day"]["PrecipitationProbability"] + day["Night"]["PrecipitationProbability"]) / 2
        thunderstorm_probability = (day["Day"]["ThunderstormProbability"] + day["Night"]["ThunderstormProbability"]) / 2

        mean_temperature += temperature
        mean_wind_speed += wind_speed
        mean_precipitation_probability += precipitation_probability
        mean_thunderstorm_probability += thunderstorm_probability

    mean_temperature //= len(data)
    mean_wind_speed //= len(data)
    mean_precipitation_probability //= len(data)
    mean_thunderstorm_probability //= len(data)

    return rate_forecast_by_metrics(
        mean_temperature,
        mean_wind_speed,
        mean_thunderstorm_probability,
        mean_precipitation_probability,
    )

def get_custom_forecast(
    temperature,
    wind_speed,
    thunderstorm_probability,
    precipitation_probability
):
    return rate_forecast_by_metrics(
        temperature,
        wind_speed,
        thunderstorm_probability,
        precipitation_probability,
    )
