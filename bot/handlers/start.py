from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from bot.utils.weather_requests import try_get_forecast

from bot.keyboards.all_kb import main_kb, cities_count_inline_kb, retry_inline_kb, cities_enter_inline_kb, change_city_inline_kb, time_range_inline_kb
from aiogram.fsm.context import FSMContext

commands_router = Router()

class Route(StatesGroup):
    cities_count = State()
    cities = State()
    city_idx = State()
    city = State()
    time_range = State()

    cities_inline_message = State()
    get_city_message = State()


@commands_router.message(CommandStart())
async def start_command(message: Message):
    text = """
Привет!
 
 Я умею предсказывать и анализировать погоду в городах на определенное время. И помогу тебе, например, оценить \
условия для путешествий! 

Давай скорее начнем
    """

    await message.answer(text, reply_markup=main_kb(message.from_user.id))

@commands_router.message(F.text == "/help")
@commands_router.message(F.text == "📖 Помощь")
async def help_command(message: Message):
    text = """
Помощь в использовании:

    /weather - запускает процесс создания маршрута для прогноза

    /help - помощь

    /start - стартовое меню
    """

    await message.answer(text)


@commands_router.message(F.text == "/weather")
@commands_router.message(F.text == "📝 Узнать прогноз")
async def weather_command(message: Message, state: FSMContext):

    await message.answer("Сколько будет городов в маршруте?", reply_markup=cities_count_inline_kb())
    await state.set_state(Route.cities_count)


@commands_router.callback_query(F.data.contains("route_cities_count"), Route.cities_count)
async def get_route_cities_count(call : CallbackQuery, state: FSMContext):
    cities_count = int(call.data.split(":")[1])

    await call.message.delete()
    await state.update_data(cities_count=cities_count)
    await state.update_data(cities=[None for _ in range(cities_count)])

    text="""
Супер!
 
Теперь давай начнем вводить города. 
 
Заметь, что первый и последний город это пункты отправления и назначения!
    """

    cities_message = await call.message.answer(text=text, reply_markup=cities_enter_inline_kb(cities_count))

    await state.update_data(cities_inline_message=cities_message)
    await state.set_state(Route.cities)


@commands_router.callback_query(F.data.contains("change_city"), Route.cities)
async def update_route_city(call : CallbackQuery, state: FSMContext):
    city_idx = call.data.split(":")[1]

    await state.update_data(city_idx=city_idx)

    text = "Введи название города:"

    get_city_message = await call.message.answer(text=text, reply_to_message_id=call.message.message_id, city_idx=city_idx)

    await call.answer(show_alert=False)
    await state.update_data(get_city_message=get_city_message)
    await state.set_state(Route.city)


@commands_router.message(F.text, Route.city)
async def get_new_city_name(message : Message, state: FSMContext):
    data = await state.get_data()

    city_idx = int(data.get("city_idx"))
    cities_message: Message = data.get("cities_inline_message")
    get_city_message : Message = data.get("get_city_message")

    cities = data.get("cities")
    cities[city_idx] = message.text

    await get_city_message.delete()
    await message.delete()
    await cities_message.edit_reply_markup(
        reply_markup=change_city_inline_kb(message.text, city_idx, cities)
    )
    await state.update_data(cities=cities)
    await state.set_state(Route.cities)


@commands_router.callback_query(F.data == "cities_collected", Route.cities)
async def check_cities(call : CallbackQuery, state: FSMContext):
    data = await state.get_data()

    cities : list = data.get("cities")
    cities_message : Message = data.get("cities_inline_message")

    if None in cities:
        await call.answer(text="Не все города заполнены!", show_alert=True)
        return


    await cities_message.delete()
    await call.message.answer("Прекрасно! Какое время анализируем?", reply_markup=time_range_inline_kb())
    await state.set_state(Route.time_range)


@commands_router.callback_query(F.data.contains("time_range"), Route.time_range)
async def get_time_range(call : CallbackQuery, state: FSMContext):
    data = await state.get_data()

    time_range = call.data.split(":")[1]
    route_cities : list = data.get("cities")

    await call.message.delete()
    await call.answer(show_alert=False)
    await call.message.answer("Ура! Проверяем информацию...")

    response = await try_get_forecast(route_cities, time_range)

    if response["result"] == "uncorrect_cities":

        text = "Ой. Кажется мы не можем найти некоторые города.\n\n"

        cities : dict = response["values"]

        for name, suitable in cities.items():
            route_cities[route_cities.index(name)] = None

            if len(suitable) > 0:
                text += name + "\nВозможно, вы имели в виду:\n"
                text += " ".join(suitable[:min(5, len(suitable))])
            text += "\n\n"

        await state.update_data(cities=route_cities)
        await call.message.answer(text, reply_markup=retry_inline_kb())
        await state.set_state(Route.cities_count)
        return

    if response["result"] == "successful":
        text = f"Прогноз на {time_range}\n\n"
        text += f"""Результат: {"Неблагоприятные" if response["forecasts"]["rate"] == "bad" else "Хорошие"} условия\n\n"""

        forecasts: dict = response["forecasts"]["values"]

        for city, forecast in forecasts.items():

            text += f"""
{city}
Температура: {forecast["mean_temperature"]["value"]}
Скорость ветра: {forecast["mean_wind_speed"]["value"]}
Вероятность осадков: {forecast["mean_precipitation_probability"]["value"]}
Вероятность грозы: {forecast["mean_thunderstorm_probability"]["value"]}\n\n"""


        await call.message.answer(text)


    if response["result"] == "server-error":
        await call.message.answer("Не можем подключиться к серверу(", reply_markup=retry_inline_kb())
        await state.set_state(Route.cities_count)
        return


    await state.clear()


@commands_router.callback_query(F.data == "retry_enter", Route.cities_count)
async def retry_enter_cities(call : CallbackQuery, state: FSMContext):
    data = await state.get_data()

    cities_count = data.get("cities_count")
    cities = data.get("cities")
    text = """
    Хорошо, давай заново начнем вводить города. 

    Заметь, что первый и последний город это пункты отправления и назначения!
        """

    cities_message = await call.message.answer(text=text, reply_markup=cities_enter_inline_kb(cities_count, cities))

    await call.answer(show_alert=False)
    await state.update_data(cities_inline_message=cities_message)
    await state.set_state(Route.cities)


@commands_router.message(F.text == "/query")
async def api_connect(message: Message):
    cities = ["Москва", "Кировград", "Багдад"]
    time_range = "12 часов"

    response = await try_get_forecast(cities, time_range)

    if response["result"] == "uncorrect_cities":

        text = "Ой. Кажется мы не можем найти некоторые города.\n\n"

        cities : dict = response["values"]

        for name, suitable in cities.items():
            text += name + "\n\nВозможно, вы имели в виду:\n"
            text += " ".join(suitable)

        await message.answer(text)

    if response["result"] == "successful":
        text = f"""Результат: {"Неблагоприятные" if response["forecasts"]["rate"] == "bad" else "Хорошие"} условия\n\n"""

        forecasts : dict = response["forecasts"]["values"]

        for city, forecast in forecasts.items():
            text += f"""
{city}

Температура: {forecast["mean_temperature"]["value"]}
Скорость ветра: {forecast["mean_wind_speed"]["value"]}
Вероятность осадков: {forecast["mean_precipitation_probability"]["value"]}
Вероятность грозы: {forecast["mean_thunderstorm_probability"]["value"]}\n\n"""

        await message.answer(text)

    if response["result"] == "limit":
        await message.answer("The allowed number of requests has been exceeded.")