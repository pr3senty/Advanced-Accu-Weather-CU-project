from City import City
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input, State, ALL, ctx, MATCH
from flask import Flask, request, abort
import plotly.express as px
from CityManager import CityManager
from logic import get_suitable_cities
from rate_forecast import analyze_forecast, rate_forecast_by_metrics, get_custom_forecast, METRICS
from api_requests import get_forecast, RequestsExceeded
from enum_classes import TimeRange
import json
from decouple import config


# PROPERTIES
MAX_ADDITION_POINTS = 3
MAX_GRAPGS = 3
apikey = ""

server = Flask(__name__)
app = Dash(
    suppress_callback_exceptions=True,
    server=server,
    external_stylesheets=["./static/index.css"],
    external_scripts=["https://kit.fontawesome.com/65351d6da2.js"])

cities : list[City] = []

@server.post("/api/")
def api_response():
    data = request.json

    route_cities, time_range = data.values()
    time_range = TimeRange.get(time_range)
    output = {}

    city_for_each_point : list[City] = []
    for city in route_cities:
        match, suitable_cities = get_suitable_cities(city, cities)

        if not match:
            output[city] = [x.name for x in suitable_cities]
            continue

        city_for_each_point.append(suitable_cities[0])

    if len(output) > 0:
        output = {"result": "uncorrect_cities", "values": output}
        return output

    forecast_for_each_city = {}

    for city in city_for_each_point:
        try:
            forecast = get_forecast(city, time_range, apikey)
        except RequestsExceeded as e:
            abort(400, str(e))

        analyzed_forecast = analyze_forecast(forecast, time_range, include_dataframe=False)

        forecast_for_each_city[city.name] = analyzed_forecast

    forecast_rate = "bad" if any([analyzed_forecast["rate"] == "bad" for analyzed_forecast in forecast_for_each_city.values()]) else "good"

    output = {"result": "successful", "forecasts": {"rate": forecast_rate, "values": forecast_for_each_city}}

    return output


app.layout = html.Div(className="content", children=[
    dcc.Store(
        id="all-forecasts",
        storage_type="memory",
        data="",
    ),
    dcc.Store(id="current-route", storage_type="memory", data={}),

    html.H1("Сервис проверки погодных условий"),
    html.Div(id="forecast-form", children=[
        dcc.Input(type="text", id="start-point", placeholder="Пункт отправления", value=""),
        html.Div(
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "6px"
            },
            id="additional-points",
            children=[]),
        html.Button("Добавить промежуточный пункт", id="add-route-point-button", n_clicks=0),
        dcc.Input(type="text", id="end-point", placeholder="Пункт назначения", value=""),
        dcc.Dropdown(
            style={"textAlign": "center", "padding": "15px", "borderRadius": 20},
            options=TimeRange.values(),
            id="time-range",
            placeholder="Выберите значение",
            value=""),
        html.Button("Проверить", id="get-forecast-button", n_clicks=0)
    ]),

    html.Div(id="result", children=[
    ])
])

@callback(
    Output("additional-points", "children", allow_duplicate=True),
    Output("add-route-point-button", "hidden", allow_duplicate=True),
    Input("add-route-point-button", "n_clicks"),
    State("additional-points", "children"),
    prevent_initial_call=True
)
def add_route_point(n_clicks, additional_children):
    children = additional_children

    if len(children) < 3:
        children.append(
            html.Div(
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "flexBasis": "100%",
                    "width": "100%"
                },
                children=[
                dcc.Input(
                    style={
                        "width": "100%",
                        "marginRight": "20px"
                    },
                    type="text",
                    id={"type": "addition-route-point", "index": n_clicks},
                    value="",
                    placeholder=f"Промежуточный пункт {len(children) + 1}"),
                html.Button(
                    id={"type": "remove-addition-route-point", "index": len(children)},
                    children=html.I(className="fa-solid fa-circle-xmark"),
                    n_clicks=0),
         ]))

        if len(children) == 3:
            return children, True


    return children, False

@callback(
    Output("additional-points", "children"),
    Output("add-route-point-button", "hidden"),
    Input({"type": "remove-addition-route-point", "index": ALL}, "n_clicks"),
    State("additional-points", "children"),
    State("add-route-point-button", "hidden"),
    prevent_initial_call=True,
)
def remove_additional_route_point(values, additional_points, add_button_is_hidden):
    triggered_id = ctx.triggered_prop_ids

    first_triggered_idx = list(triggered_id.values())[0]["index"]

    if len(triggered_id) > 1 or values[first_triggered_idx] == 0:
        return additional_points, add_button_is_hidden

    additional_points = [additional_points[i] for i in range(len(additional_points)) if i != first_triggered_idx]

    for i in range(len(additional_points)):
        additional_points[i]["props"]["children"][1]["props"]["id"]["index"] = i
        additional_points[i]["props"]["children"][0]["props"]["placeholder"] = f"Промежуточный пункт {i + 1}"


    return additional_points, False


@callback(
    output=dict(
        result=Output("result", "children"),
        forecasts_df_json=Output("all-forecasts", "data"),
        current_route_cities=Output("current-route", "data"),
        forecast_button_disabled=Output("get-forecast-button", "disabled", allow_duplicate=True)
    ),
    inputs=dict(
        _=Input("get-forecast-button", "n_clicks")
    ),
    state=dict(
        start_point=State("start-point", "value"),
        additional_points=State({"type": "addition-route-point", "index": ALL}, "value"),
        end_point=State("end-point", "value"),
        time_range=State("time-range", "value"),
        forecasts_df_json=State("all-forecasts", "data"),
    ),
    prevent_initial_call=True
)
def forecast_form(start_point, additional_points, end_point, time_range, forecasts_df_json: str, _):
    output = check_empty_fields(start_point, end_point, time_range)
    df_forecasts = pd.DataFrame(columns=[
            "City",
            "TimeRange",
            "Temperature",
            "WindSpeed",
            "PrecipitationProbability",
            "ThunderstormProbability",
            "DateTime"
        ], dtype=float) if len(forecasts_df_json) == 0 else pd.read_json(forecasts_df_json, orient="index")

    # has empty fields
    if len(output) > 0:
        return dict(result=output, forecasts_df_json=forecasts_df_json, current_route_cities=[], forecast_button_disabled=False)

    if time_range not in TimeRange.values():
        return dict(result=html.P(
            "Неизвестное значение времени для анализа. Выберите подходящее из списка!",
            className="red"
        ), forecasts_df_json=forecasts_df_json, current_route_cities=[], forecast_button_disabled=False)

    suitable_cities_for_each_point = [
        get_suitable_cities(start_point, cities),
        *[
            get_suitable_cities(point, cities)
            for point in additional_points
            if len(point) > 0
        ],
        get_suitable_cities(end_point, cities)
    ]


    city_for_each_point = []
    # check if incorrect or unknown city name
    for i, entry in enumerate(suitable_cities_for_each_point):
        match, suitable_cities = entry

        if not match:
            point_name = "промежуточного пункта " + str(i)

            if i == 0:
                point_name = "пункта отправления"
            if i == len(suitable_cities_for_each_point) - 1:
                point_name = "пункта назначения"

            output.append(
                html.P("Неизвестный город для " + point_name, className="red")
            )

            output.append(
                html.P("Возможно это")
            )

            for city in suitable_cities:
                output.append(
                    html.P(city.name)
                )
        else:
            city_for_each_point.append(suitable_cities[0])

    if len(output) > 0:
        return dict(result=output, forecasts_df_json=forecasts_df_json, current_route_cities=[], forecast_button_disabled=False)

    forecast_for_each_city = {}
    time_range = TimeRange.get(time_range)

    cities_in_row = 3
    forecast_for_each_city_by_rows = []

    sub = []
    # get analyzed forecast for each city
    for city in city_for_each_point:

        if len(df_forecasts[(df_forecasts["City"] == str(city)) & (df_forecasts["TimeRange"] == str(time_range))]) == 0:
            try:
             forecast = get_forecast(city, time_range, apikey)
            except RequestsExceeded as e:
                return dict(result=html.P(
                    str(e),
                    className="red"
                ), forecasts_df_json=forecasts_df_json, current_route_cities=[], forecast_button_disabled=False)

            analyzed_forecast = analyze_forecast(forecast, time_range)

            city_df = analyzed_forecast["dataframe"]

            city_df["City"] = city.uuid
            city_df["TimeRange"] = str(time_range)

            df_forecasts = pd.concat([df_forecasts, city_df], axis=0)
        else:
            analyzed_forecast = rate_forecast_by_metrics(
                df_forecasts[
                    (df_forecasts["City"] == city.uuid) &
                    (df_forecasts["TimeRange"] == str(time_range))
                ],
                include_dataframe=False
            )

        sub.append((city.name, analyzed_forecast))

        if len(sub) == cities_in_row:
            forecast_for_each_city_by_rows.append(sub.copy())
            sub = []

    forecast_for_each_city_by_rows.append(sub)

    forecast_rate = "bad" if any([analyzed_forecast["rate"] == "bad" for analyzed_forecast in forecast_for_each_city.values()]) else "good"


    output += [
        html.P(children=[
            "Результат: ",
            html.Span("Неблагоприятные" if forecast_rate == "bad" else "Хорошие", className=forecast_rate),
            " условия"
        ]),
        *[
            html.Div(className="cities-group", children=[
                html.Div(children=[
                    html.H3(city_name),
                    html.P(children=[
                        "Температура: ",
                        html.Span(
                            str(forecast["mean_temperature"]["value"]) + "°C",
                            className=forecast["mean_temperature"]["rate"])
                    ]),
                    html.P(children=[
                        "Скорость ветра: ",
                        html.Span(
                            str(forecast["mean_wind_speed"]["value"]) + " км/ч",
                            className=forecast["mean_wind_speed"]["rate"]
                        )
                    ]),
                    html.P(children=[
                        "Вероятность осадков: ",
                        html.Span(
                            str(forecast["mean_precipitation_probability"]["value"]) + "%",
                            className=forecast["mean_precipitation_probability"]["rate"]
                        )
                    ]),
                    html.P(children=[
                        "Вероятность грозы: ",
                        html.Span(
                            str(forecast["mean_thunderstorm_probability"]["value"]) + "%",
                            className=forecast["mean_thunderstorm_probability"]["rate"]
                        )
                    ])
                ])
                for city_name, forecast in forecast_for_each_city_by_rows[i]
            ])
            for i in range(len(forecast_for_each_city_by_rows))
        ],
        html.Div(id="graphs", children=[], style={"display":"flex", "gap": "10px", "flexDirection": "column"}),
        html.Button("Добавить график", id="add-graph-button", n_clicks=0, style={"marginTop": "15px"})
    ]

    df_forecasts = df_forecasts.reset_index()
    del df_forecasts["index"]

    return dict(
        result=output,
        forecasts_df_json=df_forecasts.to_json(orient="index"),
        current_route_cities=[city.uuid for city in city_for_each_point],
        forecast_button_disabled=False
    )


@app.callback(
    Output("get-forecast-button", "disabled"),
    Input("get-forecast-button", "n_clicks"),
    prevent_initial_call=True,
)
def disable_forecast_button(_):
    return True


@app.callback(
    Output("graphs", "children", allow_duplicate=True),
    Output("add-graph-button", "hidden", allow_duplicate=True),
    Input("add-graph-button", "n_clicks"),
    State("current-route", "data"),
    State("graphs", "children"),
    prevent_initial_call=True,
)
def add_graph(_, current_route_cities_uuid : list, current_graphs):
    cities_names = [CityManager.find_by_uuid(city_uuid) for city_uuid in current_route_cities_uuid] + ["All"]

    output = [
        html.Div(
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "6px",
                "borderRadius": "20px",
                "backgroundColor": "#8B6D5C"
            },
            className="graph-group",
            children=[
            html.Button(
                children=html.I(className="fa-solid fa-circle-xmark"),
                id={"type": "remove-graph-button", "index": len(current_graphs)},
                n_clicks=0,
                style={
                    "alignSelf": "self-end"
                }),
            dcc.Dropdown(cities_names, multi=True, id={"type": "dropdown-choice-cities", "index": len(current_graphs)}, value="All"),
            dcc.Dropdown(METRICS, id={"type": "dropdown-choice-metric", "index": len(current_graphs)}, value=""),
            dcc.Dropdown(TimeRange.values(), id={"type": "dropdown-choice-time-range", "index": len(current_graphs)}, value=""),
            dcc.Graph(
                style={"marginBottom": "20px"},
                id={"type": "dynamic-weather-graph", "index": len(current_graphs)}, figure=px.line())
        ])
    ]

    if len(current_graphs) + 1 == MAX_GRAPGS:
        return current_graphs + output, True

    return current_graphs + output, False


@app.callback(
    Output("graphs", "children"),
    Output("add-graph-button", "hidden"),
    Input({"type": "remove-graph-button", "index": ALL}, "n_clicks"),
    State("graphs", "children"),
    State("add-graph-button", "hidden"),
    prevent_initial_call=True,
)

def remove_graph(values, current_graphs, button_is_hidden):
    triggered_id = ctx.triggered_prop_ids

    first_triggered_idx = list(triggered_id.values())[0]["index"]

    if len(triggered_id) > 1 or values[first_triggered_idx] == 0:
        return current_graphs, button_is_hidden

    current_graphs = [current_graphs[i] for i in range(len(current_graphs)) if i != first_triggered_idx]

    for i in range(len(current_graphs)):
        current_graphs[i]["props"]["children"][0]["props"]["id"]["index"] = i

    return current_graphs, False


@app.callback(
    Output({"type": "dynamic-weather-graph", "index": MATCH}, "figure"),
    Input({"type": "dropdown-choice-cities", "index": MATCH}, "value"),
    Input({"type": "dropdown-choice-metric", "index": MATCH}, "value"),
    Input({"type": "dropdown-choice-time-range", "index": MATCH}, "value"),
    State("all-forecasts", "data"),
    State("current-route", "data"),
    State({"type": "dynamic-weather-graph", "index": MATCH}, "figure"),
    prevent_initial_call=True,
)
def update_graph(filter_cities, metric, time_range, all_forecasts, route_cities, current_figure):

    if len(filter_cities) == 0 or len(metric) == 0 or len(time_range) == 0:
        return current_figure

    df = pd.read_json(all_forecasts, orient="index")
    time_range = TimeRange.get(time_range)

    cities_uuid = [CityManager.find_by_name(city_name).uuid for city_name in filter_cities] if "All" not in filter_cities else route_cities

    df = df[df["City"].isin(cities_uuid)]

    df = df[df["TimeRange"] == str(time_range)]
    df["City"] = df["City"].apply(lambda uuid: CityManager.find_by_uuid(uuid))

    fig = px.line(df, x="DateTime", y=metric, color="City")

    return fig


def check_empty_fields(start_point, end_point, time_range) -> list:
    output = []

    if len(start_point) == 0:
        output.append(html.P("Вы забыли заполнить стартовую точку", className="red"))

    if len(end_point) == 0:
        output.append(html.P("Вы забыли заполнить конечную точку", className="red"))

    if len(time_range) == 0:
        output.append(html.P("Вы забыли заполнить промежуток для анализа", className="red"))

    return output



if __name__ == "__main__":

    # load api key
    apikey = config("apikey")

    # load cities
    with open("cities.json", encoding="utf-8") as file:
        data = json.load(file)

        for uuid, info in data.items():
            ru_name, en_name = info["translated_city_names"].values()

            cities.append(
                City(uuid, ru_name, info)
            )

            cities.append(
                City(uuid, en_name, info)
            )

        CityManager.init(cities)

    app.run(debug=True)