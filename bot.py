import random

import telebot
from telebot import types

from config import token
from deck_of_cards import *
from services import *
from db_services import *

TIME_TO_TAKE_BONUS = 3600  # Перерыв между получением бонуса в секундах
BONUS_SIZE = 400         # Размер бонуса
START_BALANCE = 500      # Начальный баланс


class Player:
    def __init__(self):
        self.user_id = None
        self.username = None
        self.balance = 0
        self.cards_list = []
        self.suits_list = []
        self.values = 0
        self.time_get_bonus = None
        self.bet = 0

    def get_balance(self):
        return self.balance

    def get_bet(self):
        return self.bet

    def place_a_bet(self, money):
        """Поставить ставку игроку"""
        if money <= self.balance:
            self.balance -= money
            self.bet = money
            update_balance_bd(cash=self.balance, user_id=self.user_id)
            return True
        else:
            return False

    def take_card(self):
        """Выдача карты игроку"""
        self.cards_list.append(random.choice(list(PIPS.items())))
        self.suits_list.append(random.choice(list(SUITS)))
        if len(self.cards_list) == 2 and (self.cards_list[0][0] == self.cards_list[1][0] == 'Туз'):
            self.values = 21
        else:
            self.values += self.cards_list[-1][1]

    def clear_stack(self):
        """Очистить стэк карт для новой игры"""
        self.cards_list = []
        self.suits_list = []
        self.values = 0

    def increase_balance(self, money):
        """Увеличить баланс"""
        self.balance += money
        update_balance_bd(cash=self.balance, user_id=self.user_id)

    def take_bonus(self):
        """Получить бонус"""
        if (datetime.now() - self.time_get_bonus).seconds > TIME_TO_TAKE_BONUS:
            self.time_get_bonus = datetime.now()
            self.increase_balance(BONUS_SIZE)
            write_time_to_bd(dtime=str(datetime.now()), user_id=self.user_id)

            answer = f'\U0001F381 Вы получили бонус\n\nТеперь ваш баланс составляет {sep_balance(self.get_balance())}$' \
                     f'\n\n\U0001F550 Получить следующий бонус можно через' \
                     f' {(TIME_TO_TAKE_BONUS - (datetime.now() - self.time_get_bonus).seconds) // 60} минут'
        else:
            answer = f'\U0001F4A2 Вы недавно получили бонус, следующий можно будет получить через' \
                     f' {(TIME_TO_TAKE_BONUS - (datetime.now() - self.time_get_bonus).seconds) // 60} минут.'

        return answer


player_dict = {}
dealer_dict = {}
bot = telebot.TeleBot(token)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    """Обработка сообщений"""
    if message.text == '/menu' or message.text == '\U000025AA Меню' or message.text == '/start':
        menu(message)

    if message.text == '\U0001F0CF Играть':
        play_game(message)

    if message.text == '\U0001F4B0 Баланс':
        balance(message.chat.id)

    if message.text == '\U0001F3C6 ТОП':
        show_stat(message.chat.id)

    if message.text == '\U0001F4D1 Правила':
        show_rules(message.chat.id)

    if message.text == '\U0001F381 Получить бонус':
        get_bonus(message.chat.id)

    if message.text == '\U0001F503 Сыграть ещё':
        play_game(message)


def show_keyboard() -> object:
    """Вывод клавиатуры на экран"""
    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.row('Взять', 'Хватит')
    return keyboard


def menu(message):
    """Главное меню"""
    query = find_player_db(message.from_user.id)
    if not query:
        add_player_db(user_id=message.from_user.id, username=message.from_user.username, start_balnce=START_BALANCE)
        return

    player = Player()
    player.user_id = message.from_user.id
    player.username = message.from_user.username
    player.balance = int(query[0].get('balance'))
    player.time_get_bonus = from_str_to_date(query[0].get('time_get_bonus'))
    player_dict[player.user_id] = player

    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.row('\U0001F0CF Играть', )
    keyboard.row('\U0001F4B0 Баланс', '\U0001F3C6 ТОП', '\U0001F4D1 Правила')
    text_menu = '\U000025AA Меню'
    bot.send_message(message.chat.id, text_menu, reply_markup=keyboard)


def show_stat(chat_id):
    """Показывает статистику лучших игроков"""
    stat = '\U0001F3C6 Рейтинг лучших игроков:\n\n'
    response = get_stat_from_db()
    for i in range(7):
        if i == 0:
            stat += '\U0001F947'
        elif i == 1:
            stat += '\U0001F948'
        elif i == 2:
            stat += '\U0001F949'
        else:
            stat += '{0:^4d}'.format(i+1)
        if i < len(response):
            stat += f' - {response[i].get("username")} - {sep_balance(response[i].get("balance"))}$\n'
        else:
            stat += ' - --- - ---$\n'
    bot.send_message(chat_id, stat)


def show_rules(chat_id):
    """Показывает правила игры"""
    answer = '\U0001F3AF Цель игры: Набрать 21 очко\n\n' \
             '\U0001F0CF Игрок и дилер набирают карты, выигрывает тот, кто максимально приблизится к 21 очку,' \
             ' но не больше, иначе - проигрыш\n\n' \
             '\U00002660 Значения:\n' \
             'Валет - 2 очка\n' \
             'Дама - 3 очка\n' \
             'Король - 4 очка\n' \
             'Туз - 11 очков'
    bot.send_message(chat_id, answer)


def balance(chat_id):
    """Показать баланс"""
    player = player_dict.get(chat_id)
    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.row('\U000025AA Меню', '\U0001F381 Получить бонус')
    sep_balance(player.get_balance())
    answer = f'\U0001F4B8 Ваш баланс: {sep_balance(player.get_balance())}$'
    bot.send_message(chat_id, answer, reply_markup=keyboard)


def get_bonus(chat_id):
    """Получить бонус"""
    player = player_dict.get(chat_id)
    answer = player.take_bonus()
    bot.send_message(chat_id, answer)


def play_game(message):
    """Играть"""
    player = player_dict.get(message.chat.id)
    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.row('\U000025AA Меню')
    keyboard.row('\U0001F4B3 Баланс: ' + sep_balance(player.get_balance()) + '$')
    bot.send_message(message.chat.id, 'Какую сумму вы хотите поставить?', reply_markup=keyboard)
    if message.text == '\U000025AA Меню':
        bot.send_message(message.chat.id, 'Чтобы выйти, нажмите меню ещё раз')
        return
    bot.register_next_step_handler(message, place_a_bet)


def place_a_bet(message):
    """Сделать ставку"""
    player = player_dict.get(message.chat.id)

    try:
        bet = abs(int(message.text))
    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректную сумму')
        play_game(message)
    else:
        if player.place_a_bet(bet):
            start_game(message, bet)
        else:
            bot.send_message(message.chat.id, 'У вас нет столько денег(')
            play_game(message)


def start_game(message, bet):
    """Начало игры"""
    dealer = Player()
    dealer_dict[message.chat.id] = dealer
    player = player_dict.get(message.chat.id)

    dealer.clear_stack()
    player.clear_stack()

    while dealer.values < 18:
        dealer.take_card()

    player.take_card()
    player.take_card()

    dealer_answer = f'Карты дилера:\n\n{dealer.suits_list[0]} {dealer.cards_list[0][0]} | [?]'
    player_answer = send_answer_to_player(player.values, player.cards_list, player.suits_list)
    keyboard = show_keyboard()

    bot.send_message(message.chat.id, dealer_answer)
    bot.send_message(message.chat.id, player_answer, reply_markup=keyboard)
    if player.values == 21:
        stop_game(message, bet)
    else:
        bot.register_next_step_handler(message, game_step)


def game_step(message):
    """
    Взять - игрок берет дополнительную карту
    Хватит - набор карт прекращается
    """
    dealer = dealer_dict.get(message.chat.id)
    player = player_dict.get(message.chat.id)

    bet = player.get_bet()

    if message.text == 'Взять':
        player.take_card()
        if player.values < 21:
            answer = send_answer_to_player(values=player.values, cards_list=player.cards_list,
                                           suits_list=player.suits_list)
            keyboard = show_keyboard()
            bot.send_message(message.chat.id, answer, reply_markup=keyboard)
            bot.register_next_step_handler(message, game_step)
        else:
            answer = send_answer_to_player(values=player.values, cards_list=player.cards_list,
                                           suits_list=player.suits_list)
            bot.send_message(message.chat.id, answer, reply_markup=types.ReplyKeyboardRemove())
            stop_game(message, bet)

    elif message.text == 'Хватит':
        stop_game(message, bet)


def stop_game(message, bet):
    """
    Игра прекращается если:
    -Игрок нажал кнопку "Хватит"
    -У игрока значение больше, чем 21
    -У игрока значение равно 21
    """
    player = player_dict.get(message.chat.id)
    dealer = dealer_dict.get(message.chat.id)

    dealer_answer = f'Карты дилера:\n\n'
    dealer_answer += send_answer_to_player(dealer.values, dealer.cards_list, dealer.suits_list)
    bot.send_message(message.chat.id, dealer_answer)

    if (player.values <= 21) and ((player.values > dealer.values) or (dealer.values > 21)):
        score_answer = f'\U00002705 Вы выиграли\n\nДилер: {dealer.values}\nВы: {player.values}'
        player.increase_balance(bet * 2)
    elif ((player.values == dealer.values) and (player.values <= 21)) or (player.values > 21 and dealer.values > 21):
        score_answer = f'\U000026AA Вы сыграли вничью\n\nДилер: {dealer.values}\nВы: {player.values}'
        player.increase_balance(bet)
    else:
        score_answer = f'\U0000274C Вы проиграли\n\nДилер: {dealer.values}\nВы: {player.values}'

    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.row('\U000025AA Меню', '\U0001F503 Сыграть ещё')
    bot.send_message(message.chat.id, score_answer, reply_markup=keyboard)


bot.polling(none_stop=True)
