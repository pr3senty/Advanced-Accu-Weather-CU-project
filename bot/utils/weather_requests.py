import requests
import asyncio
import json

from urllib3.exceptions import MaxRetryError


async def api_connect(cities, time_range):
    response = requests.post(
        "http://127.0.0.1:8050/api/",
        headers={
            "Content-Type": "application/json; charset=UTF-8",

        },
        json={
            "cities": cities,
            "time_range": time_range
        }
    )

    return response

async def try_get_forecast(cities, time_range):

    try:
        response = await asyncio.Task(api_connect(cities, time_range))
    except Exception:
        return {"result": "server-error"}

    if response.status_code == 500:
        return {"result": "limit"}

    return json.loads(response.text)