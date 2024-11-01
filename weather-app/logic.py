from City import City


def get_suitable_cities(target_city: str, cities : list[City]):
    ma : tuple[list[City], int] = ([], 10 ** 10)

    target_city = target_city.lower()
    for city_entry in cities:
        city = city_entry.name.lower()

        if target_city == city:
            ma = ([city_entry], 0)
            break

        i = 0
        for j in range(len(target_city)):
            if len(city) == i:
                break

            if target_city[j] == city[i]:
                i += 1

        not_match = max(0, len(target_city) - len(city)) + len(city) - i

        if not_match < ma[1]:
            ma = ([city_entry], not_match)
        elif not_match == ma[1]:
            ma[0].append(city_entry)


    match = (
            (ma[1] == 0 or (ma[1] == 1 and ma[0][0].name[-1] != target_city[-1] and target_city[-1] in "аеуы"))
            and len(ma[0]) == 1
    )

    return match, ma[0]

