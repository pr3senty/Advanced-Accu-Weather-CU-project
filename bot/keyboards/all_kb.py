from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, KeyboardButtonPollType, InlineQueryResult, \
    InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_kb(user_telegram_id: int) -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="📖 Помощь"),],
        [KeyboardButton(text="📝 Узнать прогноз")]
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Что делаем?"
    )

    return keyboard


def cities_count_inline_kb():
    builder = InlineKeyboardBuilder()

    builder.row(*[
        InlineKeyboardButton(text=str(i), callback_data=f"route_cities_count:{i}")
        for i in range(2, 5 + 1)
    ])

    return builder.as_markup()

def cities_enter_inline_kb(cities_count, custom=[]):
    builder = InlineKeyboardBuilder()

    for i in range(cities_count):
        text = f"Промежуточный пункт {i}"

        if i == 0:
            text = "Пункт отправления"

        if i == cities_count - 1:
            text = "Пункт прибывания"

        if len(custom) == cities_count and custom[i] is not None:
            text = custom[i]

        builder.row(
            InlineKeyboardButton(text=text, callback_data=f"change_city:{i}")
        )

    builder.row(
        InlineKeyboardButton(text="Готово", callback_data="cities_collected")
    )

    return builder.as_markup()


def retry_inline_kb():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="Ввести заново", callback_data="retry_enter")
    )

    return builder.as_markup()


def change_city_inline_kb(city, idx, cities: list):
    builder = InlineKeyboardBuilder()

    for i in range(len(cities)):
        if i == idx:
            builder.row(
                InlineKeyboardButton(text=city, callback_data=f"change_city:{i}")
            )

            continue

        text = f"Промежуточный пункт {i}"

        if i == 0:
            text = "Пункт отправления"

        if i == len(cities) - 1:
            text = "Пункт прибывания"

        builder.row(
            InlineKeyboardButton(text=text if cities[i] is None else cities[i], callback_data=f"change_city:{i}")
        )

    builder.row(
        InlineKeyboardButton(text="Готово", callback_data="cities_collected")
    )

    return builder.as_markup()


def time_range_inline_kb():
    builder = InlineKeyboardBuilder()

    for time_range in ["12 часов", "5 дней"]:
        builder.row(
            InlineKeyboardButton(text=time_range, callback_data=f"time_range:{time_range}")
        )

    return builder.as_markup()

def create_spec_kb():
    kb_list = [
        [KeyboardButton(text="Отправить гео", request_location=True)],
        [KeyboardButton(text="Поделиться номером", request_contact=True)],
        [KeyboardButton(text="Отправить викторину/опрос", request_poll=KeyboardButtonPollType())]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list,
                                   resize_keyboard=True,
                                   one_time_keyboard=True,
                                   input_field_placeholder="Воспользуйтесь специальной клавиатурой:")
    return keyboard