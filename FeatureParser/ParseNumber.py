import re

"""
Функция извлекает из подаваемой строки первое число float64 "." или "," в качестве разделителя, возвращает ошибку, если в подаваемой строке нет чисел

:param s: строка, из которой извлекается число

:return: первое число из s в типе float64, позиция числа в строке
"""
def parse_number(s):
    # У числа s строчного типа "," меняется на "." затем число преобразуется к типу float
    try:
        m = re.search("\d+[.,]?\d*", s)
        loc = m.span()
        num = float(re.findall("\d+[.,]?\d*", s)[0].replace(",", "."))
        num = float(s[loc[0]:loc[1]].replace(",", "."))
    except:
        num = None
        loc = None
    return num, loc