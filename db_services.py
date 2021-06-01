import pymysql.cursors
from config import host, user, password, db_name


def get_connection():
    """Соединение с БД"""
    connection = pymysql.connect(host=host,
                                 user=user,
                                 password=password,
                                 db=db_name,
                                 charset='utf8',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def db_query(sql: str) -> list:
    """Запрос в БД"""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(sql)
    query = cursor.fetchall()
    connection.commit()
    connection.close()
    return query


def add_player_db(user_id: int, username: str, start_balnce):
    """Добавление игрока в БД"""
    sql = f'INSERT Player(user_id, username, balance) VALUES ({user_id}, "{username}", {start_balnce})'
    db_query(sql)


def find_player_db(user_id: int):
    """Поиск игрока по БД"""
    sql = f'SELECT * FROM Player WHERE user_id = "{user_id}"'
    plr = db_query(sql)
    return plr


def update_balance_bd(cash: int, user_id: int):
    """Обновление баланса в бд"""
    sql = f'UPDATE Player SET balance = {cash} WHERE user_id = "{user_id}"'
    db_query(sql)


def write_time_to_bd(dtime: str, user_id: int):
    """Записывает время получения бонуса в бд"""
    sql = f'UPDATE Player SET time_get_bonus = "{dtime}" WHERE user_id = {user_id};'
    db_query(sql)


def get_stat_from_db():
    """Возвращает 7 игроков, сортируя по убыванию баланса"""
    sql = 'SELECT username, balance FROM Player ORDER BY balance DESC LIMIT 7;'
    stat = db_query(sql)
    return stat