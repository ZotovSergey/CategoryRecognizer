import re

import FeatureParser.Patterns as Patterns

spaces_line_regexp = r"^\s+$"

class FeatureParser:
    """
    Содержит шаблоны для поиска характеристики и другие параметры
    """
    def __init__(self, config):
        # Составление алгоритмов отбора значений признаков по заданной конфигурации

        #   Список функций для поиска характеристик в SKU по шаблонам из конфигурационного файла
        self.parse_func_chain = []
        #   Значение характеристики по умолчанию (если не сработал ни один из шаблонов)
        self.default_val = ""

        #   Добавление функций по паттернам
        if "Patterns" in config:
            patterns_config_arr = config["Patterns"]
            for pattern_config in patterns_config_arr:
                pattern = pattern_type_select(pattern_config)
                self.parse_func_chain.append(pattern.parse)
        #   Добавление значения по умолчанию
        if "DefaultValue" in config:
            self.default_val = config["DefaultValue"]
    
    def parse(self, sku):
        """
        Функция поиска значения характеристики в sku

        :param sku string: строка SKU, в которой осуществляется поиск значения характеристики

        :return: значение характеристики в формате строки, определенное по строке sku, если строка sku пустая или состоит из пробелов, возвращается пустая строка
        """
        # Проверка, является ли строка sku пустой или состоящей из пробелов; если это не так, то идет парсинг характеристики, иначе возвращается нулевое значение
        if len(sku) > 0 and re.search(spaces_line_regexp, sku) is None:
            # Перебор всех функций self.parse_func_chain, по которым будет определяться значение характеристики по sku
            for i, pattern_func in enumerate(self.parse_func_chain):
                char_val, loc = pattern_func(sku)
                #print(i)
                # Если значение характеристики было найдено, то оно после дальнейшей обработки будет возвращено, иначе проводится поиск по следующему шаблону
                if char_val is not None:
                    return [char_val]
            return [self.default_val]
        return [""]
    
    def parse_and_remove(self, sku):
        """
        Функция поиска значения характеристики в sku

        :param sku string: строка SKU, в которой осуществляется поиск значения характеристики

        :return: значение характеристики в формате строки, определенное по строке sku, если строка sku пустая или состоит из пробелов, возвращается пустая строка
        """
        # Проверка, является ли строка sku пустой или состоящей из пробелов; если это не так, то идет парсинг характеристики, иначе возвращается нулевое значение
        if len(sku) > 0 and re.search(spaces_line_regexp, sku) is None:
            # Перебор всех функций self.parse_func_chain, по которым будет определяться значение характеристики по sku
            for i, pattern_func in enumerate(self.parse_func_chain):
                char_val, loc = pattern_func(sku)
                # Если значение характеристики было найдено, то оно после дальнейшей обработки будет возвращено, иначе проводится поиск по следующему шаблону
                if char_val is not None:
                    removed_feature_sku = " ".join([sku[:loc[0]], sku[loc[1]:]])
                    return [char_val, removed_feature_sku]
            return [self.default_val, sku]
        return ["", sku]

def pattern_type_select(pattern_param_dict):
    """
    Выбор типа шаблона по строчному названию, из карты параметров pattern_dict с ключом "Type". Возвращает функцию парсинга характеристики по SKU, соответствующую выбранному шаблону.
    Существуют типы шаблонов:
    Обозначение "Val" означает шаблон числового значения;
    Обозначение "Const" означает шаблон постоянного строчного значения.

    :param patternMap map[string]interface{}: карта параметров шаблона

    :return: функция парсинга характеристики по SKU, соответствующую выбранному шаблону, если шаблон под полученным обозначением существует
    """
    # Библиотека параметров создаваемого паттерна
    pattern_param = pattern_param_dict["Pattern"]
    # Тип функции парсинга характеристики по SKU и выбор типа функции
    func_type = pattern_param_dict["Type"]
    # Шаблон числового значения
    pattern = ""
    if func_type == "Val":
        pattern = Patterns.ValuePattern(pattern_param)
    # Шаблон постоянного строчного значения
    if func_type == "Const":
        pattern = Patterns.ConstValuePattern(pattern_param)
    # Если не найдено ни одно подходящее обозначение типа, возвращается пустое значение
    return pattern