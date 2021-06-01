from datetime import *


def from_str_to_date(time_str: str):
    """Переводит строку даты в объект datetime"""
    time_tuple = datetime(year=int(time_str[0:4]), month=int(time_str[5:7]), day=int(time_str[8:10]),
                          hour=int(time_str[11:13]), minute=int(time_str[14:16]), second=int(time_str[17:19]),
                          microsecond=int(time_str[20:-1]))
    return time_tuple


def sep_balance(money: int) -> str:
    """Разделение суммы точками"""
    res = ''
    if money == 0:
        return '0'
    i = 1
    while money != 0:
        if i % 4 == 0:
            res += '.'
        res += str(money % 10)
        money //= 10
        i += 1
    return res[::-1]


def send_answer_to_player(values: int, cards_list: list, suits_list: list, dop_message='') -> str:
    """Подготовка ответа игроку"""
    answer = f'Ваше значение: {values}\n'
    for i in range(len(cards_list)):
        answer += f'{suits_list[i]} {cards_list[i][0]} | '
    answer += dop_message
    return answer


