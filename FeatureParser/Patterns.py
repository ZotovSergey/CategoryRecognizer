import numpy as np
import re

import FeatureParser.TypeConverters as TypeConverters
from FeatureParser.ParseNumber import parse_number

"""
Содержит шаблон для поиска числового значения характеристики и перевода его в строчный вид
"""
class ValuePattern:
    def __init__(self, pattern_param_dict):
        # Приставка, добавляемая к каждой записи
        self.prefix = ""
        # Суффикс, добавляемый к каждой записи
        self.suffix = ""
        # Список шаблонов для поиска диапазона слева
        self.left_range_pat_arr = []
        # Список шаблонов для поиска диапазона справа
        self.right_range_pat_arr = []
        # Знак диапазона, используемый в записи
        self.range_symbol = []
        # Функция, определяющее числовое значение характеристики, соответствующее шаблону
        self.value_parse_func = None
	    # Функция, приводящая числовое значение к строчному
        self.value_to_str_func = None
        # Значения параметров шаблона по умолчанию, если их нет в pattern_param
        name = ""
        mult = 1.
        min_val = 0.
        max_val = np.inf
        multiplicity = 0
        prefix = ""
        suffix = ""
        left_add_pat_arr = []
        right_add_pat_arr = []
        add_val_pat_arr = []
        left_mult_pat_arr = []
        right_mult_pat_arr = []
        mult_val_pat_arr = []
        left_range_pat_arr = []
        right_range_pat_arr = []
        range_val_pat_arr = []
        range_symbol = []
        exceptions_arr = []

        # Регулярное выражение (строковое) для поиска индикатора в SKU, если его нет в patternParam, возвращается ошибка
        if "Reg" in pattern_param_dict:
            reg = pattern_param_dict["Reg"]
            # Парсинг названия шаблона
            if "Name" in pattern_param_dict:
                name = pattern_param_dict["Name"]
            # Парсинг значения множителя числового значения характеристики, если он есть в описании шаблона в конфигурационном файле
            if "Mult" in pattern_param_dict:
                mult = pattern_param_dict["Mult"]
            # Парсинг минимального числового значения характеристики, если он есть в описании шаблона в конфигурационном файле
            if "MinVal" in pattern_param_dict:
                min_val = pattern_param_dict["MinVal"]
            # Парсинг максимального числового значения характеристики, если он есть в описании шаблона в конфигурационном файле
            if "MaxVal" in pattern_param_dict:
                max_val = pattern_param_dict["MaxVal"]
            # Парсинг кратности
            if "Multiplicity" in pattern_param_dict:
                multiplicity = pattern_param_dict["Multiplicity"]
            # Парсинг приставки числового значения характеристики, если он есть в описании шаблона в конфигурационном файле
            if "Prefix" in pattern_param_dict:
                prefix = pattern_param_dict["Prefix"]
            # Парсинг суффикса числового значения характеристики, если он есть в описании шаблона в конфигурационном файле
            if "Suffix" in pattern_param_dict:
                suffix = pattern_param_dict["Suffix"]
            # Составление регулярных выражений для поиска слагаемых с найденным числовым значением характеристики слева и справа, для этого в описании шаблона в конфигурационном файле должны быть
			# регулярные выражения для символов сложения и для самого слогаемого
            if "AddendumPatterns" in pattern_param_dict:
                add_patterns = pattern_param_dict["AddendumPatterns"]
                if "AddSymbolPatterns" in pattern_param_dict:
                    add_symbol_patterns = pattern_param_dict["AddSymbolPatterns"]
                    left_add_pat_arr, right_add_pat_arr = side_reg_symb_val(add_patterns, add_symbol_patterns)
                    add_val_pat_arr = add_patterns[:len(left_add_pat_arr)]
            # Составление регулярных выражений для поиска множителей числового значения характеристики слева и справа, для этого в описании шаблона в конфигурационном файле должны быть
			# регулярные выражения для символов умножения и для самого множителя
            if "MultPatterns" in pattern_param_dict:
                mult_patterns = pattern_param_dict["MultPatterns"]
                if "MultSymbolPatterns" in pattern_param_dict:
                    mult_symbol_patterns = pattern_param_dict["MultSymbolPatterns"]
                    left_mult_pat_arr, right_mult_pat_arr = side_reg_symb_val(mult_patterns, mult_symbol_patterns)
                    mult_val_pat_arr = mult_patterns[:len(left_mult_pat_arr)]
            # Составление регулярных выражений для поиска диапазона числовых значений характеристики слева и справа, для этого в описании шаблона в конфигурационном файле должны быть
			# регулярные выражения для символов диапазона и для самого второго значения, а также знак диапазона, который ставится между значениями
            if "RangeBorderPatterns" in pattern_param_dict:
                range_border_patterns = pattern_param_dict["RangeBorderPatterns"]
                if "RangeSymbolPatterns" in pattern_param_dict:
                    range_symbol_patterns = pattern_param_dict["RangeSymbolPatterns"]
                    if "RangeSymbol" in pattern_param_dict:
                        range_symbol = pattern_param_dict["RangeSymbol"]
                        left_range_pat_arr, right_range_pat_arr = side_reg_symb_val(range_border_patterns, range_symbol_patterns)
                        range_val_pat_arr = range_border_patterns[:len(left_range_pat_arr)]
            # Составление регулярных выражений для поиска полных исключений
            if "Exceptions" in pattern_param_dict:
                exceptions_arr = pattern_param_dict["Exceptions"]
            
            num_val_pat = NumberValuePattern(
                reg,
                name,
                mult,
                min_val,
                max_val,
                multiplicity,
                left_add_pat_arr,
                right_add_pat_arr,
                add_val_pat_arr,
                left_mult_pat_arr,
                right_mult_pat_arr,
                mult_val_pat_arr,
                exceptions_arr
            )
            # Функция, определяющее числовое значение характеристики, соответствующее шаблону; по умолчанию проверка соответствий регулярному выражению идет с приоритетом соответствиям
            # слева, если в параметрах шаблона обозначено, что reverseSearch - правда, то преоритет будет для соответствий справа
            value_parse_func = num_val_pat.parse_straight
            if "Order" in pattern_param_dict:
                order = pattern_param_dict["Order"]
                if order == "Reverse":
                    value_parse_func = num_val_pat.parse_reverse
                if order == "Sum":
                    value_parse_func = num_val_pat.parse_sum
                if order == "Max":
                    value_parse_func = num_val_pat.parse_max
                if order == "Min":
                    value_parse_func = num_val_pat.parse_min

            # Выбор функции, приводящей числовое значение к строчному
            converter = TypeConverters.NumToStrConvertor(None)
            if "ValueType" in pattern_param_dict:
                value_type = pattern_param_dict["ValueType"]
                round_count_match = re.search("\d+$", value_type)
                round_count = None
                if round_count_match is not None:
                    round_count_loc = round_count_match.span()
                    round_count = int(value_type[round_count_loc[0] : round_count_loc[1]])
                    value_type = value_type[:round_count_loc[0]]
                if value_type == "Int":
                    converter = TypeConverters.NumToStrConvertor(0)
                if value_type == "Float":
                    converter = TypeConverters.NumToStrConvertor(round_count)
                if value_type == "FloatComma":
                    converter = TypeConverters.NumToStrConvertor(round_count, True)
                value_to_str_func = converter.transform
            self.prefix = prefix
            self.suffix = suffix
            self.left_range_pat_arr = left_range_pat_arr
            self.right_range_pat_arr = right_range_pat_arr
            self.range_val_pat_arr = range_val_pat_arr
            self.range_symbol = range_symbol
            self.value_parse_func = value_parse_func
            self.value_to_str_func = value_to_str_func
    
    """
    Поиск характеристики в SKU по шаблону valuePattern

    :param sku: SKU по которому определяется характеристика

    :return: характеристика, полученная по шаблону valuePattern в виде строки
    """
    def parse(self, sku):
        # Приведение SKU к нижнему регистру
        sku_low = sku.lower()
        num_val, match_loc, name = self.value_parse_func(sku_low)
        if num_val is not None:
            # Поиск диапазона по регулярным выражениям
            val_range = self.find_range(sku_low, match_loc, num_val)
            if val_range is not None:
                val_str = "".join([self.value_to_str_func(val_range[0]), self.range_symbol, self.value_to_str_func(val_range[1])])
            else:
                val_str = self.value_to_str_func(num_val)
            # Значение возвращается с приставкой и суффиксом
            return "".join([self.prefix, val_str, self.suffix]), match_loc, name
        return None, match_loc, name

    """
    Поиск обозначения диапазона в SKU по потенциальному первому значению диапазона (или второго) и его расположению в SKU

    :param sku: SKU, в котором ведется поиск значения диапазона
    :param match_loc: границы расположения потенциального первого значения диапазона в SKU
    :param first_range_val: числовое значение первого значения диапазона

    :return: если второе значение диапазона найдено, возвращаются оба значения в массиве в порядке возрастания и true, иначе возвращается пустой массив и false
    """
    def find_range(self, sku, match_loc, first_range_val):
        # Поиск всех значений, удовлетворяющих паттерну диапазона слева и справа от первого значения
        second_range_val = find_add_val(sku, match_loc, self.left_range_pat_arr, self.right_range_pat_arr, self.range_val_pat_arr)
        # Определение порядка значений диапазона (порядок возрастания, если значения равны, считается, что диапазон не найден)
        range_num = None
        if second_range_val is not None:
            if first_range_val > second_range_val:
                range_num = [second_range_val, first_range_val]
            else:
                if first_range_val < second_range_val:
                    range_num = [first_range_val, second_range_val]
        return range_num

"""
Содержит основные параметры поиска числового значения характеристики, которое можно найти по данному шаблону и основные функции, с помощью которых проводится поиск значения в строке SKU
"""
class NumberValuePattern:
    def __init__(self, reg, name, mult, min_val, max_val, multiplicity, left_add_pat_arr, right_add_pat_arr, add_val_pat_arr, left_mult_pat_arr, right_mult_pat_arr, mult_val_pat_arr, exceptions_arr):
        # Регулярное выражение для поиска индикатора характеристики
        self.reg = reg
        # Название шаблона
        self.name = name
        # Множитель массы из индикатора
        self.mult = mult
        # Минимальное значение допустимое при использовании данного шаблона
        self.min_val = min_val
        # Максимальное значение допустимое при использовании данного шаблона
        self.max_val = max_val
        # Допустимая кратность значения полученного значения
        self.multiplicity = multiplicity
        
        # Список шаблонов для поиска слагаемого слева
        self.left_add_pat_arr = left_add_pat_arr
        # Список шаблонов для поиска слагаемого справа
        self.right_add_pat_arr = right_add_pat_arr
        # Список шаблонов для поиска значений слагаемых
        self.add_val_pat_arr = add_val_pat_arr
        # Список шаблонов для поиска множителя слева
        self.left_mult_pat_arr = left_mult_pat_arr
        # Список шаблонов для поиска множителя справа
        self.right_mult_pat_arr = right_mult_pat_arr
        # Список шаблонов для поиска значений множителей
        self.mult_val_pat_arr = mult_val_pat_arr
        # Список шаблонов для полных исключений
        self.exceptions_arr = exceptions_arr

    """
    Поиск значения характеристики с плавающей точкой по строке sku, согласно условиям из структуры pattern, в прямом порядке (значение слева sku преоритетней)

    :param sku: строка, в которой ведется поиск числового значения характеристики

    :return: самое левое найденное значение характеристики с плавающей точкой; локация найденного соответствия ошибка, если характеристика не найдена
    """
    def parse_straight(self, sku):
        # Поиск всех границ соответствий регулярному выражению self.reg
        matches = self.find_matches(sku)
        # Перебор всех соответствий в прямом порядке (слева направо)
        for m in matches:
            # Парсинг числа float64 из найденного соответствия
            loc_borders = m.span()
            # Проверка наличия исключений
            if not self.find_exception(sku, loc_borders):
                val, num_loc = self.parse_char_from_match(sku, loc_borders)
                # Если число в соответствии найдено, поиск завершается
                if val is not None:
                    loc = num_loc + loc_borders[0]
                    return val, loc, self.name
        # Если ни один вариант не подошел или не было найдено ни одно соответствие регулярному выражению, функция прекращает работу, а характеристика считается не найденной
        return None, None, None
    
    """
    Поиск значения характеристики с плавающей точкой по строке sku, согласно условиям из структуры pattern, в обратном порядке (значение справа sku преоритетней)

    :param sku: строка, в которой ведется поиск значения характеристики

    :return: самое правое найденное значение характеристики с плавающей точкой; локация найденного соответствия ошибка, если характеристика не найдена
    """
    def parse_reverse(self, sku):
        # Поиск всех границ соответствий регулярному выражению self.reg
        matches = self.find_matches(sku)
        matches.reverse()
        # Перебор всех соответствий в обратном порядке (справа налево)
        for m in matches:
            # Парсинг числа float64 из найденного соответствия
            loc_borders = m.span()
            # Проверка наличия исключений
            if not self.find_exception(sku, loc_borders):
                val, num_loc = self.parse_char_from_match(sku, loc_borders)
                # Если число в соответствии найдено, поиск завершается
                if val is not None:
                    loc = [num_loc[0] + loc_borders[0], num_loc[1] + loc_borders[0]]
                    return val, loc, self.name
        # Если ни один вариант не подошел или не было найдено ни одно соответствие регулярному выражению, функция прекращает работу, а характеристика считается не найденной
        return None, None, None
    
    """
    Поиск и сложение значений характеристик с плавающей точкой по строке sku, согласно условиям из структуры pattern

    :param sku: строка, в которой ведется поиск значения характеристики

    :return: сумма всех найденных значений характеристик с плавающей точкой; возвращается нулевое значение локации
    """
    def parse_sum(self, sku):
        # Поиск всех границ соответствий регулярному выражению self.reg
        matches = self.find_matches(sku)
        val = 0
        # Перебор и сложение всех соответствий
        for m in matches:
            # Парсинг числа float64 из найденного соответствия
            loc_borders = m.span()
            # Проверка наличия исключений
            if not self.find_exception(sku, loc_borders):
                val_cond, num_loc = self.parse_char_from_match(sku, loc_borders)
                if val_cond is not None:
                    val += val_cond
            # Если число в соответствии найдено, поиск завершается
        if val > 0:
            return val, [0, 0], self.name
        # Если ни один вариант не подошел или не было найдено ни одно соответствие регулярному выражению, функция прекращает работу, а характеристика считается не найденной
        return None, None, None

    """
    Поиск максимального значения характеристики с плавающей точкой по строке sku, согласно условиям из структуры pattern

    :param sku: строка, в которой ведется поиск значения характеристики

    :return: максимальное значение из всех найденных значений характеристик с плавающей точкой; локация найденного соответствия ошибка, если характеристика не найдена
    """
    def parse_max(self, sku):
        # Поиск всех границ соответствий регулярному выражению self.reg
        matches = self.find_matches(sku)
        val = 0
        loc_borders = [0, 0]
        # Перебор и сложение всех соответствий
        for m in matches:
            # Парсинг числа float64 из найденного соответствия
            loc_borders_cond = m.span()
            # Проверка наличия исключений
            if not self.find_exception(sku, loc_borders):
                val_cond = self.parse_char_from_match(sku, loc_borders_cond)
                if val_cond > val:
                    val = val_cond
                    loc_borders = loc_borders_cond
            # Если число в соответствии найдено, поиск завершается
        if val > 0:
            return val, loc_borders, self.name
        # Если ни один вариант не подошел или не было найдено ни одно соответствие регулярному выражению, функция прекращает работу, а характеристика считается не найденной
        return None, None, None

    """
    Поиск минимального значения характеристики с плавающей точкой по строке sku, согласно условиям из структуры pattern

    :param sku: строка, в которой ведется поиск значения характеристики

    :return: минимальное значение из всех найденных значений характеристик с плавающей точкой; локация найденного соответствия ошибка, если характеристика не найдена
    """
    def parse_min(self, sku):
        # Поиск всех границ соответствий регулярному выражению self.reg
        matches = self.find_matches(sku)
        val = np.inf
        loc_borders = [0, 0]
        # Перебор и сложение всех соответствий
        for m in matches:
            # Парсинг числа float64 из найденного соответствия
            loc_borders_cond = m.span()
            # Проверка наличия исключений
            if not self.find_exception(sku, loc_borders):
                val_cond = self.parse_char_from_match(sku, loc_borders_cond)
                if val_cond < val:
                    val = val_cond
                    loc_borders = loc_borders_cond
            # Если число в соответствии найдено, поиск завершается
        if val < np.inf:
            return val, loc_borders, self.name
        # Если ни один вариант не подошел или не было найдено ни одно соответствие регулярному выражению, функция прекращает работу, а характеристика считается не найденной
        return None, None, None

    """
    Поиск в некотором части строки sku, ограниченной локацией matchLoc значения характеристики, удовлетворяющего шаблону, а также поиск дополнительного множителя характеристики

    :param sku: строка, в которой ведется поиск числового значения характеристики
    :param char_loc: локация (номера первого и последнего символов) соответствия регулярному выражению в строке sku

    :return: найденное числовое значение характеристики; ошибка, если подходящее значение не найодено
    """
    def parse_char_from_match(self, sku, char_loc):
        # Парсинг числа float64 из найденного соответствия
        ind_val, loc = parse_number(sku[char_loc[0] : char_loc[1]])
        val = None
        if ind_val is not None:
            # Найденное число умножается на множитель из шаблона pattern.mult записывается в качестве найденной массы, также проводится поиск множителей и слагаемых справа или слева от
		    # найденного числового значения характеристики по регулярным выражениям pattern.leftMultPatArr и pattern.rightMultPatArr и характеристика умножается на найденный дополнительный множитель
            val = (ind_val + self.find_add_addendum(sku, char_loc)) * self.mult * self.find_add_mult(sku, char_loc)
            # Определяется, соответствует найденная масса допустимым значениям из шаблона
            if not ((val >= self.min_val) and (val <= self.max_val)):
                # Если верно, то характеристика считается найденной и функция заканчивает работу, значение характеристики переписывается в строку и к ней добавляется суффикс
                val = None
            # Проверка кратности
            elif not ((self.multiplicity == 0) or (val % self.multiplicity == 0)):
                # Если верно, то характеристика считается найденной и функция заканчивает работу, значение характеристики переписывается в строку и к ней добавляется суффикс
                val = None
        return val, loc

    """
    Функция поиска соответствий в SKU по регулярным выражениям

    :param sku: строка, в которой было найдено числовое значение характеристики и ведется поиск множителя

    :return: найдено ли исключение
    """
    def find_matches(self, sku):
        matches = []
        if isinstance(self.reg, str):
            for m in re.finditer(self.reg, sku):
                matches.append(m)
        else:
            if "SelfReg" in self.reg:
                for match in re.finditer(self.reg["SelfReg"], sku):
                    loc = match.span()
                    if "LeftReg" in self.reg:
                        left_found = False
                        left_reg = self.reg["LeftReg"]
                        m = re.search(left_reg, sku[:loc[0]])
                        if m is not None:
                            left_found = True
                    else:
                        left_found = True
                    if left_found:
                        if "RightReg" in self.reg:
                            right_found = False
                            right_reg = self.reg["RightReg"]
                            m = re.search(right_reg, sku[loc[1]:])
                            if m is not None:
                                right_found = True
                        else:
                            right_found = True
                        if right_found:
                            matches.append(match)
        return matches

    """
    Функция поиска исключений в SKU слева и справа от найденного числового значения характеристики по регулярным выражениям

    :param sku: строка, в которой было найдено числовое значение характеристики и ведется поиск множителя
    :param charLoc: локация (номера первого и последнего символов) числового значения характеристики в строке sku

    :return: найдено ли исключение
    """
    def find_exception(self, sku, char_loc):
        for exception_reg_dict in self.exceptions_arr:
            if "LeftReg" in exception_reg_dict:
                left_found = False
                left_exp_reg = exception_reg_dict["LeftReg"]
                m = re.search(left_exp_reg, sku[:char_loc[0]])
                if m is not None:
                    left_found = True
            else:
                left_found = True
            if left_found:
                if "RightReg" in exception_reg_dict:
                    right_found = False
                    right_exp_reg = exception_reg_dict["RightReg"]
                    m = re.search(right_exp_reg, sku[char_loc[1]:])
                    if m is not None:
                        right_found = True
                else:
                    right_found = True
                if right_found:
                    if "SelfReg" in exception_reg_dict:
                        self_found = False
                        self_exp_reg = exception_reg_dict["SelfReg"]
                        m = re.search(self_exp_reg, sku[char_loc[0] : char_loc[1]])
                        if m is not None:
                            self_found = True
                    else:
                        self_found = True
                    if self_found:
                        return True
        return False

    """
    Функция поиска слагаемого характеристики в SKU слева и справа от найденного числового значения характеристики по регулярным выражениям pattern.leftMultPatArr и pattern.rightMultPatArr,
    соответственно

    :param sku: строка, в которой было найдено числовое значение характеристики и ведется поиск множителя
    :param charLoc: локация (номера первого и последнего символов) числового значения характеристики в строке sku

    :return: множитель числового значения характеристики или 1, если такой множитель не найден
    """
    def find_add_addendum(self, sku, char_loc):
        add = 0.
        add_cond = find_add_val(sku, char_loc, self.left_add_pat_arr, self.right_add_pat_arr, self.add_val_pat_arr)
        if add_cond is not None:
            add = add_cond
        return add
    
    """
    Функция поиска множителя характеристики в SKU слева и справа от найденного числового значения характеристики по регулярным выражениям pattern.leftMultPatArr и pattern.rightMultPatArr,
    соответственно

    :param sku string: строка, в которой было найдено числовое значение характеристики и ведется поиск множителя
    :param char_loc []int: локация (номера первого и последнего символов) числового значения характеристики в строке sku

    :return: множитель числового значения характеристики или 1, если такой множитель не найден
    """
    def find_add_mult(self, sku, char_loc):
        mult = 1.
        mult_cond = find_add_val(sku, char_loc, self.left_mult_pat_arr, self.right_mult_pat_arr, self.mult_val_pat_arr)
        if mult_cond is not None:
            mult = mult_cond
        return mult

"""
Функция поиска дополнительного значения характеристики в SKU слева и справа от найденного числового значения характеристики по регулярным выражениям leftPatternArr и rightPatternArr,
соответственно

:param sku: строка, в которой было найдено числовое значение характеристики и ведется поиск
:param char_loc: локация (номера первого и последнего символов) числового значения характеристики в строке sku
:param left_pattern_arr: массив регулярных выражений для поиска дополнительных значение слева от основного
:param right_pattern_arr: массив регулярных выражений для поиска дополнительных значение справа от основного
:param val_pattern_arr: массив регулярных выражений для поиска значений допольнительных значений

:return: дополнительное значение характеристики, если оно найдено; флаг, показывающий, что значение найдено
"""
def find_add_val(sku, char_loc, left_pattern_arr, right_pattern_arr, val_pattern_arr):
    # Часть строки sku слева от найденного соответствии
    sku_left_part = sku[:char_loc[0]]
    # Часть строки sku справа от найденного соответствии
    sku_right_part = sku[char_loc[1]:]
    # Перебор регулярных выражений множителей слева или справа
    for i in range(len(left_pattern_arr)):
        # Поиск левого дополнительного значения слева от индикатора характеристики в sku
        found_mult_arr = []
        for m in re.finditer(left_pattern_arr[i], sku_left_part):
            found_mult_arr.append(m)
        # Если найден хотя бы один множитель
        if len(found_mult_arr) > 0:
            # Из последнего (самого правого) из найденных множитилей извлекается число
            b = found_mult_arr[-1].span()
            left_add = sku_left_part[b[0] : b[1]]
            str_val_arr = []
            for m in re.finditer(val_pattern_arr[i], left_add):
                str_val_arr.append(m)
            add_val, loc = parse_number(left_add[str_val_arr[-1].span()[0] : str_val_arr[-1].span()[1]])
            # Если число извлечено верно, цикл прерывается, а значение найденного дополнительного значения и возвращается
            if add_val != None:
                return add_val
        # Поиск первого правого дополнительного значения (самого левого) справа от индикатора характеристики в sku
        for m in re.finditer(right_pattern_arr[i], sku_right_part):
            found_mult_arr.append(m)
        # Если найден хотя бы один множитель
        if len(found_mult_arr) > 0:
            # Из найденного дополнительного значения извлекается число
            b = found_mult_arr[0].span()
            right_add = sku_right_part[b[0] : b[1]]
            str_val_arr = []
            for m in re.finditer(val_pattern_arr[i], right_add):
                str_val_arr.append(m)
            add_val, loc = parse_number(right_add[str_val_arr[-1].span()[0] : str_val_arr[-1].span()[1]])
            # Если число извлечено верно, цикл прерывается, а значение найденного дополнительного значения и возвращается
            if add_val != None:
                return add_val
    return None


"""
Функция составляет сочетания регулярных выражений значений и символов/разделителей для нахождения справа и слева от оснолвного выражения

:param val_reg_str_arr: массив строчных регулярных выражений некоторых значений
:param symb_reg_str_arr []string: массив строчных регулярных выражений символов/разделителей

:return: два массива регулярных выражений для чтения значений, соответствующих valRegStrArr через разделитель, соответствующий symbRegStrArr справа или слева
"""
def side_reg_symb_val(val_reg_str_arr, symb_reg_str_arr):
    left_pattern_arr = []
    right_pattern_arr = []
    # Перебор всех регулярных выражений сочетаний знаков множителей из конфигураций
    mult_reg_count = min([len(symb_reg_str_arr), len(val_reg_str_arr)])
    for i in range(mult_reg_count):
        # Составление регулярного выражения для определения множителя характеристики слева и справа
        left_pattern_arr.append("".join([val_reg_str_arr[i], symb_reg_str_arr[i], "$"]))
        right_pattern_arr.append("".join(["^", symb_reg_str_arr[i], val_reg_str_arr[i]]))
    return left_pattern_arr, right_pattern_arr

"""
Содержит шаблон для поиска постоянного значения характеристики - некоторые условия
"""
class ConstValuePattern:
    def __init__(self, pattern_param_dict):
        # Регулярное выражение (строковое) для поиска индикатора в SKU, если его нет в patternParam, возвращается ошибка
        self.reg = ""
        if "Reg" in pattern_param_dict:
            self.reg = pattern_param_dict["Reg"]
            # Константное значение характеристики, если его нет в patternParam, используется пустая строка
            self.val = ""
            if "Val" in pattern_param_dict:
                self.val = pattern_param_dict["Val"]

    """
    Поиск соответствий регулярному выражению pattern.reg в строке sku, указывающей на то, что характеристика имеет константное значение, записанное в pattern.val
    """
    def parse(self, sku):
        # Приведение SKU к нижнему регистру
        sku_low = sku.lower()
        # Поиск соответствия в строке sku
        match_arr = re.search(self.reg, sku_low)
        # Если найдено хотя бы одно соответствие, возвращается соответствующее значение из pattern
        if match_arr is not None:
            return self.val, [0, 0], ""
        return None, None, None