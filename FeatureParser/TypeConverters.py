"""

"""
class NumToStrConvertor:
    def __init__(self, round_count=None, useComma=False):
        self.round_count = round_count
        self.useComma = useComma
    
    def transform(self, num):
        if self.round_count is not None:
            num = round(num, self.round_count)
        num_str = str(num).rstrip('0').rstrip('.')
        if self.useComma:
            num_str = num_str.replace(".", ",")
        return str(num).rstrip('0').rstrip('.')

# """
# Трансформация числа float в целое число, написанное в строке

# :param num: трансформированное число

# :return: строчное выражение (string) целой части числа num
# """
# def float_to_str_int(num):
#     return str(int(round(num)))

# """
# Трансформация числа float в число float, написанное в строке

# :param num: трансформированное число
# :param round_count: число знаков после точки; если None, то округления не происходит

# :return: строчное выражение (string) числа с плавающей точкой num
# """
# def float_to_str_float(num, round_count=None):
#     if round_count is not None:
#         num = round(num, round_count)
#     return str(num).rstrip('0').rstrip('.')

# """
# Трансформация числа float в число float, написанное в строке, с запятой, в качетсве разделителя целой части от дробной

# :param num: трансформированное число
# :param round_count: число знаков после точки; если None, то округления не происходит

# :return: строчное выражение (string) числа с плавающей запятой num
# """
# def float_to_str_float_comma(num, round_count=None):
#     return float_to_str_float(num, round_count).replace(".", ",")