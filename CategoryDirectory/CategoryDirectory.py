import pandas as pd

from datetime import datetime

import CategoryDirectory.identify_category as identify_category_cython
from Utilities.Utilities import *

"""
Пакет, осуществляющий определение категории по SKU
"""

def features_preprocessing(features):
    """
    Предобрабатывает серию идентификаторов (pandas Series)

    :param features: серию идентификаторов в  формате pandas Series, в каждой строке серии строка, в которой идентификаторы перечисляются через знак ';'
    :return: предобработанный список идентификаторов (каждый идентификаор записан в список, который в свою очередь записан в список, соответствующий строке исходной серии)
    """
    # Замена пустых строк серии на ''
    new_features = features.fillna('')
    # Приведение идетификаторов к верхнему регистру
    new_features = new_features.str.upper()
    # Разделение строк с идентификаторами на списки с отдельными идентификаторами по разделителю ';'
    new_features = new_features.str.split(';')
    # Удаление всех пустых идентификаторов
    for row in new_features:
        while '' in row: row.remove('')
    return list(new_features)

 
class CategoryDirectory:
    """
    Справочник категорий, содержащий их обозначения и им соответствующие обозначения идентифиткаторы всех типов
    """
    def __init__(self,
                 dir_name,
                 data_path,
                 directory_sheet_name,
                 category_rightholders_title,
                 main_identifiers_title,
                 main_limit_identifiers_title,
                 add_limit_identifiers_title,
                 excluding_identifiers_title,
                 preprocessing_func,
                 set_msg_func
                 ):
        """
        :param dir_name: название составляемого справочника
        :param data_path: путь к excel-файлу, с данными для справочника
        :param directory_sheet_name: название листа содержащей информацию для справочника, если строка пустая, то берется первый лист в заданном файле
        :param category_rightholders_title: название колонки, содержащей обозначения категорий
        :param main_identifiers_title: название колонки, содержащей основные идентификаторы
        :param main_limit_identifiers_title: название колонки, содержащей основные ограничивающие идентификаторы
        :param add_limit_identifiers_title: название колонки, содержащей дополнительные ограничивающие идентификаторы
        :param excluding_identifiers_title: название колонки, содержащей исключающие идентификаторы
        :param preprocessing_func: функция предобработки SKU
        :param set_msg_func: функция вывода сообщения
        """
        try:
            # Начало отсчета времени
            timer_start = datetime.now()
            # Сообщение о начале составления справочника
            set_msg_func('Составление справочника')

            # Чтение данных из файла data_path
            with pd.ExcelFile(data_path) as reader:
                # Замена пустого значения листа со справочником а название первого листа в файле
                if len(directory_sheet_name) == 0:
                    directory_sheet_name = reader.sheet_names[0]
                # Чтение листа excel файла с названием directory_sheet_name, содержащей обозначения категорий и их идентификаторы
                features_df = pd.read_excel(reader, sheet_name=directory_sheet_name)
                # Замена значений пустых строк на соответствующие значения, если необходимо
                if len(category_rightholders_title) == 0:
                    category_rightholders_title = features_df.columns[0]
                if len(main_identifiers_title) == 0:
                    main_identifiers_title = features_df.columns[1]
                if len(main_limit_identifiers_title) == 0:
                    main_limit_identifiers_title = features_df.columns[2]
                if len(add_limit_identifiers_title) == 0:
                    add_limit_identifiers_title = features_df.columns[3]
                if len(excluding_identifiers_title) == 0:
                    excluding_identifiers_title = features_df.columns[4]

            # Добавление кавычек, если указано название
            if len(dir_name) > 0:
                dir_name = "".join(["\"", dir_name, "\""])
            # Сообщение о начале составления справочника
            set_message_with_countdown(" ".join(['Составление справочника', dir_name]), timer_start, set_msg_func)
            set_message_with_tab("".join(['по файлу \"', data_path, '\";']), set_msg_func)
            set_message_with_tab("".join(['по листу \"', directory_sheet_name, '\";']), set_msg_func)
            set_message_with_tab("".join(['столбец категорий:\"', category_rightholders_title, '\";']), set_msg_func)
            set_message_with_tab("".join(['столбец глав. ид-ов:\"', main_identifiers_title, '\";']), set_msg_func)
            set_message_with_tab("".join(['столбец глав. огран. ид-ов:\"', main_limit_identifiers_title, '\";']), set_msg_func)
            set_message_with_tab("".join(['столбец доп. огран. ид-ов:\"', add_limit_identifiers_title, '\";']), set_msg_func)
            set_message_with_tab("".join(['столбец искл. ид-ов:\"', excluding_identifiers_title, '\"']), set_msg_func)

            # Запись списка обозначений категории из features_df
            self.category_rightholders = list(features_df[category_rightholders_title])
            # Предобработка и запись списка основных идентификаторов из features_df
            self.main_identifiers = features_preprocessing(features_df[main_identifiers_title])
            # Предобработка и запись списка основных ограничивающих идентификаторов из features_df
            self.main_limit_identifiers = features_preprocessing(features_df[main_limit_identifiers_title])
            # Предобработка и запись списка дополнительных ограничивающих идентификаторов из features_df
            self.add_limit_identifiers = features_preprocessing(features_df[add_limit_identifiers_title])
            # Предобработка и запись списка исключающих идентификаторов из features_df
            self.excluding_identifiers = features_preprocessing(features_df[excluding_identifiers_title])
            # Функция предобработки SKU
            self.preprocessing_func = preprocessing_func
            
            # Сообщение о завершении составлния спраочника
            set_message_with_countdown("".join(['Справочник \"' + dir_name + '\" составлен']), timer_start, set_msg_func)
            set_message_with_tab("".join(['кол-во категорий в справочнике:\t', str(len(self.category_rightholders))]), set_msg_func)
            
        except Exception as e:
            set_error_message(str(e), timer_start, set_msg_func)

    def identify_category(self, sku_row):
        """
        Определение категории по заданному SKU.
        Заданному SKU соответствует обозначение категории из category_rightholders, если он содержит один из основных идентификаторов из соответствующего списка из self.main_identifiers,
        один из основных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifiers, если он не пустой,
        один из дополнительных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifiers, если он не пустой,
        не содержит ни одного из исключающих идентификаторов из self.excluding_identifiers.
        Работает аналогично функции identify_category_cython, но медленнее

        :param sku_row: SKU, по которому определяется категория
        :return: обозначение категории из self.category_rightholders или пустая строка, если категория не удается определить (list)
        """
        # Предобработка строки SKU
        prep_sku_row = self.preprocessing_func(sku_row)
        # Перебор всех категорий из справочника
        for i in range(len(self.category_rightholders)):
            # Перебор основых идентификаторов
            for main_id in self.main_identifiers[i]:
                # Определение, содержатся ли основной идентификатор в заданном SKU
                #   Если основной идентификатор найден
                if main_id in prep_sku_row:
                    # Флаг "ограничивающие идентификаторы найдены"
                    limit_id_found = False
                    # Если есть основные ограничивающие идентификаторы
                    if len(self.main_limit_identifiers[i]) > 0:
                        # Перебор основных ограничивающих идентификаторов
                        for main_limit_id in self.main_limit_identifiers[i]:
                            # Определение, содержатся ли основной ограничивающий идентификатор в заданном SKU
                            #   Если основной ограничивающий идентификатор найден
                            if main_limit_id in prep_sku_row:
                                # Если есть дополнительные ограничивающие идентификаторы
                                if len(self.add_limit_identifiers[i]) > 0:
                                    # Перебор дополнительных ограничивающих идентификаторов
                                    for add_limit_id in self.add_limit_identifiers[i]:
                                        # Определение, содержатся ли дополнительный ограничивающий идентификатор в заданном SKU
                                        #    Если дополнительный ограничивающий идентификатор найден
                                        if add_limit_id in prep_sku_row:
                                            # Выставляется флаг "ограничивающие идентификаторы найдены", цикл поиска дополнительных ограничивающих идентификаторов прерывается
                                            limit_id_found = True
                                            break
                                # Если дополнительных ограничивающих идентификаторов нет
                                else:
                                    # Выставляется флаг "ограничивающие идентификаторы найдены"
                                    limit_id_found = True
                            # если "ограничивающие идентификаторы найдены", цикл поиска дополнительных ограничивающих идентификаторов прерывается
                            if limit_id_found:
                                break
                    # Если основных ограничивающих идентификаторов нет
                    else:
                        # Выставляется флаг "ограничивающие идентификаторы найдены"
                        limit_id_found = True
                    # если "ограничивающие идентификаторы найдены", начинается поиск исключающих идентификаторов
                    if limit_id_found:
                        # Флаг "исключающий дентификатор найден"
                        excluding_id_found = False
                        # Перебор исключающих идентификаторов
                        for excluding_id in self.excluding_identifiers[i]:
                            # Определение, содержатся ли исключающий идентификатор в заданном SKU
                            #   Если исключающий идентификатор найден
                            if excluding_id in prep_sku_row:
                                # Выставляется флаг "исключающий дентификатор найден", цикл поиска исключающих идентификаторов прерывается
                                excluding_id_found = True
                                break
                    # Если "ограничивающие идентификаторы найдены" и не "исключающий дентификатор найден"
                    if limit_id_found and not excluding_id_found:
                        # Возвращается соответствующее обозначение категории
                        return [self.category_rightholders[i]]
        # Если не найдено ни одной подходящей категории, возвращается пустая строка
        return ['']

    def identify_category_and_dec_id(self, sku_row):
        """
        Определение категории по заданному SKU, а также вывод главного, главного ограничивающего и дополнительного ограничивающего идентификаторов, найденных в SKU и определивших
        предадлежность выбранной категории, если они есть, а иначе пустую строку.
        Заданному SKU соответствует обозначение категории из category_rightholders, если он содержит один из основных идентификаторов из соответствующего списка из self.main_identifiers,
        один из основных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifiers, если он не пустой,
        один из дополнительных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifiers, если он не пустой,
        не содержит ни одного из исключающих идентификаторов из self.excluding_identifiers.
        Работает аналогично функции identify_category_and_dec_id, но медленнее

        :param sku_row: SKU, по которому определяется категория
        :return: обозначение категории из self.category_rightholders или пустая строка, если категория не удается определить; главный решающий идентификатор; главный ограничивающий решающий
        идентификатор; дополнительный ограничивающий решающий идентификатор (list)
        """
        # Предобработка строки SKU
        prep_sku_row = self.preprocessing_func(sku_row)
        # Перебор всех категорий из справочника
        for i in range(len(self.cat_rightholders)):
            # Перебор основых идентификаторов
            for main_id in self.main_identifiers[i]:
                # Определение, содержатся ли основной идентификатор в заданном SKU
                #   Если основной идентификатор найден
                if main_id in prep_sku_row:
                    # Флаг "ограничивающие идентификаторы найдены"
                    limit_id_found = False
                    # Если есть основные ограничивающие идентификаторы
                    if len(self.main_limit_identifiers[i]) > 0:
                        # Перебор основных ограничивающих идентификаторов
                        for main_limit_id in self.main_limit_identifiers[i]:
                            # Определение, содержатся ли основной ограничивающий идентификатор в заданном SKU
                            #   Если основной ограничивающий идентификатор найден
                            if main_limit_id in prep_sku_row:
                                # Если есть дополнительные ограничивающие идентификаторы
                                if len(self.add_limit_identifiers[i]) > 0:
                                    # Перебор дополнительных ограничивающих идентификаторов
                                    for add_limit_id in self.add_limit_identifiers[i]:
                                        # Определение, содержатся ли дополнительный ограничивающий идентификатор в заданном SKU
                                        #   Если дополнительный ограничивающий идентификатор найден
                                        if add_limit_id in prep_sku_row:
                                            # Выставляется флаг "ограничивающие идентификаторы найдены", цикл поиска дополнительных ограничивающих идентификаторов прерывается
                                            limit_id_found = True
                                            # Запись кандидатов в решающие главный и дополнительный ограничивающие идинтификаторы
                                            main_limit_dec_id = main_limit_id
                                            add_limit_dec_id = add_limit_id
                                            break
                                # Если дополнительных ограничивающих идентификаторов нет
                                else:
                                    # Выставляется флаг "ограничивающие идентификаторы найдены"
                                    limit_id_found = True
                                    # Запись кандидатов в решающие главный ограничивающие идинтификатор, дополнительного ограничивающего идинтификатора нет
                                    main_limit_dec_id = main_limit_id
                                    add_limit_dec_id = ''
                            # если "ограничивающие идентификаторы найдены", цикл поиска дополнительных ограничивающих идентификаторов прерывается
                            if limit_id_found:
                                break
                    # Если основных ограничивающих идентификаторов нет
                    else:
                        # Выставляется флаг "ограничивающие идентификаторы найдены"
                        limit_id_found = True
                        # Запись кандидатов в решающие главного и дополнитльного ограничивающих идинтификаторов нет
                        main_limit_dec_id = ''
                        add_limit_dec_id = ''
                    # если "ограничивающие идентификаторы найдены", начинается поиск исключающих идентификаторов
                    if limit_id_found:
                        # Флаг "исключающий дентификатор найден"
                        excluding_id_found = False
                        # Перебор исключающих идентификаторов
                        for excluding_id in self.excluding_identifiers[i]:
                            # Определение, содержатся ли исключающий идентификатор в заданном SKU
                            #   Если исключающий идентификатор найден
                            if excluding_id in prep_sku_row:
                                # Выставляется флаг "исключающий дентификатор найден", цикл поиска исключающих идентификаторов прерывается
                                excluding_id_found = True
                                break
                    # Если "ограничивающие идентификаторы найдены" и не "исключающий дентификатор найден"
                    if limit_id_found and not excluding_id_found:
                        # Возвращается соответствующее обозначение категории
                        return [self.category_rightholders[i], main_id, main_limit_dec_id, add_limit_dec_id]
        # Если не найдено ни одной подходящей категории, возвращается пустая строка
        return ['', '', '', '']
    
    # def identify_category_and_history(self, sku_row):
    #     """
        
    #     """
    #     history = []
    #     # Перебор всех категорий из справочника
    #     for i in range(len(self.category_rightholders)):
    #         # Перебор основых идентификаторов
    #         for main_id in self.main_identifiers[i]:
    #             # Определение, содержатся ли основной идентификатор в заданном SKU
    #             #   Если основной идентификатор найден
    #             if main_id in sku_row:
    #                 main_limit_id_found = False
    #                 # Флаг "ограничивающие идентификаторы найдены"
    #                 limit_id_found = False
    #                 # Флаг "исключающий дентификатор найден"
    #                 excluding_id_found = False
    #                 # Если есть основные ограничивающие идентификаторы
    #                 if len(self.main_limit_identifiers[i]) > 0:
    #                     # Перебор основных ограничивающих идентификаторов
    #                     for main_limit_id in self.main_limit_identifiers[i]:
    #                         # Определение, содержатся ли основной ограничивающий идентификатор в заданном SKU
    #                         #   Если основной ограничивающий идентификатор найден
    #                         if main_limit_id in sku_row:
    #                             main_limit_id_found = True
    #                             # Если есть дополнительные ограничивающие идентификаторы
    #                             if len(self.add_limit_identifiers[i]) > 0:
    #                                 # Перебор дополнительных ограничивающих идентификаторов
    #                                 for add_limit_id in self.add_limit_identifiers[i]:
    #                                     # Определение, содержатся ли дополнительный ограничивающий идентификатор в заданном SKU
    #                                     #   Если дополнительный ограничивающий идентификатор найден
    #                                     if add_limit_id in sku_row:
    #                                         # Выставляется флаг "ограничивающие идентификаторы найдены", цикл поиска дополнительных ограничивающих идентификаторов прерывается
    #                                         limit_id_found = True
    #                                         break
    #                             # Если дополнительных ограничивающих идентификаторов нет
    #                             else:
    #                                 # Выставляется флаг "ограничивающие идентификаторы найдены"
    #                                 limit_id_found = True
    #                         # если "ограничивающие идентификаторы найдены", цикл поиска дополнительных ограничивающих идентификаторов прерывается
    #                         if limit_id_found:
    #                             break
    #                 # Если основных ограничивающих идентификаторов нет
    #                 else:
    #                     # Выставляется флаг "ограничивающие идентификаторы найдены"
    #                     limit_id_found = True
    #                 # если "ограничивающие идентификаторы найдены", начинается поиск исключающих идентификаторов
    #                 if limit_id_found:
    #                     # Флаг "исключающий дентификатор найден"
    #                     excluding_id_found = False
    #                     # Перебор исключающих идентификаторов
    #                     for excluding_id in self.excluding_identifiers[i]:
    #                         # Определение, содержатся ли исключающий идентификатор в заданном SKU
    #                         #   Если исключающий идентификатор найден
    #                         if excluding_id in sku_row:
    #                             # Выставляется флаг "исключающий дентификатор найден", цикл поиска исключающих идентификаторов прерывается
    #                             excluding_id_found = True
    #                             break
    #                 history_note = 'Кондидат: \"' + self.category_rightholders[i] + '\"; Осн. ид.: ' + main_id
    #                 if len(self.main_limit_identifiers[i]) > 0:
    #                     history_note += '; Осн. огр. ид.: '
    #                     if main_limit_id_found:
    #                         history_note += main_limit_id
    #                     else:
    #                         history_note += 'не найден'
    #                     if len(self.add_limit_identifiers[i]) > 0:
    #                         history_note += '; Доп. огр. ид.: '
    #                         if limit_id_found:
    #                             history_note += add_limit_id
    #                         else:
    #                             history_note += 'не найден'
    #                 history.append(history_note)
    #                 if excluding_id_found:
    #                     history_note += '; Искл. ид.: ' + excluding_id
    #                 # Если "ограничивающие идентификаторы найдены" и не "исключающий дентификатор найден"
    #                 if limit_id_found and not excluding_id_found:
    #                     # Возвращается соответствующее обозначение категории
    #                     return self.category_rightholders[i], '\n'.join(history)
    #     # Если не найдено ни одной подходящей категории, возвращается пустая строка
    #     return '', '\n'.join(history)

    def identify_category_cython(self, sku_row):
        """
        Определение категории по заданному SKU.
        Заданному SKU соответствует обозначение категории из category_rightholders, если он содержит один из основных идентификаторов из соответствующего списка из self.main_identifiers,
        один из основных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifiers, если он не пустой,
        один из ддополнительных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifiers, если он не пустой,
        не содержит ни одного из исключающих идентификаторов из self.excluding_identifiers.
        Работает аналогично функции identify_category, но быстрее засчет использования Cython

        :param sku_row: SKU, по которому определяется категория
        :return: обозначение категории из self.category_rightholders или пустая строка, если категория не удается определить (list)
        """
        # Предобработка строки SKU
        prep_sku_row = self.preprocessing_func(sku_row)
        return [identify_category_cython.identify_category(prep_sku_row, self.category_rightholders, self.main_identifiers, self.main_limit_identifiers, self.add_limit_identifiers, self.excluding_identifiers)]

    def identify_category_and_dec_id_cython(self, sku_row):
        """
        Определение категории по заданному SKU, а также вывод главного, главного ограничивающего и дополнительного ограничивающего идентификаторов, найденных в SKU и определивших
        предадлежность выбранной категории, если они есть, а иначе пустую строку.
        Заданному SKU соответствует обозначение категории из category_rightholders, если он содержит один из основных идентификаторов из соответствующего списка из self.main_identifiers,
        один из основных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifiers, если он не пустой,
        один из дополнительных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifiers, если он не пустой,
        не содержит ни одного из исключающих идентификаторов из self.excluding_identifiers.
        Работает аналогично функции identify_category_and_dec_id, но быстрее засчет использования Cython

        :param sku_row: SKU, по которому определяется категория
        :return: обозначение категории из self.bcategory_rightholders или пустая строка, если категория не удается определить (list)
        """
        # Предобработка строки SKU
        prep_sku_row = self.preprocessing_func(sku_row)
        return list(identify_category_cython.identify_category_and_dec_id(prep_sku_row, self.category_rightholders, self.main_identifiers, self.main_limit_identifiers, self.add_limit_identifiers, self.excluding_identifiers))

