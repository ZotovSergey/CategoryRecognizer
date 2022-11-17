import numpy as np

from datetime import datetime
from math import floor

def conv_nan(val):
    if val is np.nan:
        return None
    return val

def set_message_with_tab(msg, set_msg_func):
    """
    Вывод сообщения с табуляцией в начале

    :param msg: строка сообщения (str)
    :param set_msg_func: функция вывода сообщения (Функция)

    :return: записывает msg в окно сообщений
    """
    set_msg_func("".join(['\t', msg]))

def set_message_with_countdown(msg, start_timer, set_msg_func):
    """
    Вывод сообщения с отсчетом времени в начале

    :param msg: строка сообщения (str)
    :param start_timer: время начала отсчета (datetime)
    :param set_msg_func: функция вывода сообщения (Функция)

    :return: выводится msg с отсчетом времени в начале, согласно функции set_msg_func
    """
    set_msg_func("".join([countdown(start_timer), '\t', msg]))

def set_error_message(msg, start_timer, set_msg_func):
    """
    Вывод сообщения об ошибке с отсчетом времени в начале

    :param msg: строка сообщения (предположительно, сообщения об ошибке) (str)
    :param start_timer: время начала отсчета (datetime)
    :param set_msg_func: функция вывода сообщения (Функция)

    :return: выводится msg с обозначением ошибки и с отсчетом времени в начале, согласно функции set_msg_func
    """
    set_message_with_countdown(" ".join(["ERROR!!!", msg]), start_timer, set_msg_func)
    raise Exception("ERROR!!!")


def countdown(start_timer):
        """
        Вывод отсчета времени от заданного начала отчета времени start_timer в формате строки 'h:mm:ss'

        :param start_timer: вреия начала отсчета (datetime)

        :return: Отсчет времени от заданного начала отчета времени start_timer в формате строки 'h:mm:ss'
        """
        # Вычисление времени от начала отсчета self.proc_begin_time
        time = datetime.now() - start_timer
        # Вычисление целых часов, минут и секунд в time
        hours, reminder = divmod(time.total_seconds(), 3600)
        minutes, seconds = divmod(reminder, 60)
        hours_str = str(floor(hours))
        minutes_str = str(floor(minutes))
        # Приведение целых минут и секунд к формату mm и ss, соответственно
        if len(minutes_str) == 1:
            minutes_str = "".join(["0", minutes_str])
        seconds_str = str(floor(seconds))
        if len(seconds_str) == 1:
            seconds_str = "".join(["0", seconds_str])
        # Вывод времени в формате h:mm:ss
        return ":".join([hours_str, minutes_str, seconds_str])

class ListWraper():
    """
    Класс содержащий некоторую функцию от одной переменной и может возвращать результат работы этой функции в списке. Используется, если одиночный результат использования некоторой
    функции должен быть в списке для правильности дльнейших вычислений
    """
    def __init__(self, func):
        """
        :param func: некоторая функция от одной переменной, возвращаемое значение которой должно быть в списке
        """
        self.func = func
    
    def func_return_in_list(self, input):
        """
        Возвращает результат функции self.func от переменной input в списке
        """
        return [self.func(input)]
