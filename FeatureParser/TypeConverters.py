"""
Трансформация числа float в целое число, написанное в строке

:param num: трансформированное число

:return: строчное выражение (string) целой части числа num
"""
def float_to_str_int(num):
    return str(int(round(num)))

"""
Трансформация числа float в число float, написанное в строке

:param num: трансформированное число

:return: строчное выражение (string) числа с плавающей точкой num
"""
def float_to_str_float(num):
    return str(num).rstrip('0').rstrip('.')

"""
Трансформация числа float в число float, написанное в строке, с запятой, в качетсве разделителя целой части от дробной

:param num: трансформированное число

:return: строчное выражение (string) числа с плавающей запятой num
"""
def float_to_str_float_comma(num):
    return float_to_str_float(num).replace(".", ",")