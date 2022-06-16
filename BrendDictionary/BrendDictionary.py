import pandas as pd
import os
import pickle

import BrendDictionary.identify_brend as identify_brend_cython

"""
Пакет, осуществляющий определение бренда по SKU
"""

def load_dictionary(dict_name):
    """
    Загружает справочник о заданному пути
    :param dict_name: путь до загружаемого справочника
    :return: справочник по заданному пути, объект BrendDictionary
    """
    with open(os.path.join('saves', dict_name), 'rb') as file:
        return pickle.load(file)

def features_preprocessing(features):
    """
    Предобрабатывает серию идентификаторов (pandas Series)

    :param features: серию идентификаторов в  формате pandas Series, в каждой строке серии строка, в которой идентификаторы перечисляются через знак ';'
    :return: предобработанный список идентификаторов (каждый идентификаор записан в список, который в свою очередь записан в список, соответствующий строке исходной серии)
    """
    # Замена пустых строк серии на ''
    new_features = features.fillna('')
    # Разделение строк с идентификаторами на списки с отдельными идентификаторами по разделителю ';'
    new_features = new_features.str.split(';')
    # Удаление всех пустых идентификаторов
    for row in new_features:
        while '' in row: row.remove('')
    return list(new_features)

def find_all_dict():
    """
    Находит все сохраненные справочники в saves
    "return" список всех сохраненных в save справочников
    """
    return os.listdir('saves')


class BrendDictionary:
    """
    Справочник брендов, содержащий их обозначения и им соответствующие обозначения идентифткаторы всех типов
    """
    def __init__(self, file_path, dictinary_sheet_name,
                 brand_rightholders_title='ЗНАЧЕНИЕ К ВОЗВРАЩЕНИЮ',
                 main_identifires_title='ОСНОВНЫЕ ИДЕНТИФИКАТОРЫ КАТЕГОРИИ\n (СОДЕРЖИТ)',
                 main_limit_identifires_title='ОСНОВНЫЕ ОГРАНИЧИВАЮЩИЕ ИДЕНТИФИКАТОРЫ\n (И ОБЯЗАТЕЛЬНО СОДЕРЖИТ)',
                 add_limit_identifires_title='ДОПОЛНИТЕЛЬНЫЕ ОГРАНИЧИВАЮЩИЕ ИДЕНТИФИКАТОРЫ\n (И ТАКЖЕ ОБЯЗАТЕЛЬНО СОДЕРЖИТ)',
                 excluding_identifires_title='ИСКЛЮЧАЮЩИЕ ИДЕНТИФИКАТОРЫ\n (НЕ СОДЕРЖИТ)'):
        """
        :param file_path: путь к excel файлу, содержащему справочник
        :param dictinary_sheet_name: название книги из excel файла по пути file_path, содержащей справочник
        :param brand_rightholders_title: название колонки, содержащей обозначения брендов
        :param main_identifires_title: название колонки, содержащей основные идентификаторы
        :param main_limit_identifires_title: название колонки, содержащей основные ограничивающие идентификаторы
        :param add_limit_identifires_title: название колонки, содержащей дополнительные ограничивающие идентификаторы
        :param excluding_identifires_title: название колонки, содержащей исключающие идентификаторы
        """
        # Чтение книги excel файла по пути file_path с названием dictinary_sheet_name, содержащей обозначения брендов и их идентификаторы
        features_df = pd.read_excel(file_path, sheet_name=dictinary_sheet_name)
        # Запись списка обозначений бренда из features_df
        self.brand_rightholders = list(features_df[brand_rightholders_title])
        # Предобработка и запись списка основных идентификаторов из features_df
        self.main_identifires = features_preprocessing(features_df[main_identifires_title])
        # Предобработка и запись списка основных ограничивающих идентификаторов из features_df
        self.main_limit_identifires = features_preprocessing(features_df[main_limit_identifires_title])
        # Предобработка и запись списка дополнительных ограничивающих идентификаторов из features_df
        self.add_limit_identifires = features_preprocessing(features_df[add_limit_identifires_title])
        # Предобработка и запись списка исключающих идентификаторов из features_df
        self.excluding_identifires = features_preprocessing(features_df[excluding_identifires_title])
    
    def __len__(self):
        """
        Количество брендов в справочнике
        """
        return len(self.brand_rightholders)
    
    def identify_brend(self, sku_row):
        """
        Определение бренда по заданному SKU.
        Заданному SKU соответствует оозначение бренда из brand_rightholders, если он содержит один из основных идентификаторов из соответствующего списка из self.main_identifires,
        один из основных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifires, если он не пустой,
        один из дополнительных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifires, если он не пустой,
        не содержит ни одного из исключающих идентификаторов из self.excluding_identifires.
        Работает аналогично функции identify_brend_cython, но медленнее

        :param sku_row: SKU, по которому определяется бренд
        :return: обозначение бренда из self.brand_rightholders или пустая строка, если бренд не удается определить
        """
        # Перебор всех брендов из справочника
        for i in range(len(self.brand_rightholders)):
            # Перебор основых идентификаторов
            for main_id in self.main_identifires[i]:
                # Определение, содержатся ли основной идентификатор в заданном SKU
                pos = main_id in sku_row
                # Если основной идентификатор найден
                if pos:
                    # Флаг "ограничивающие идентификаторы найдены"
                    limit_id_found = False
                    # Если есть основные ограничивающие идентификаторы
                    if len(self.main_limit_identifires[i]) > 0:
                        # Перебор основных ограничивающих идентификаторов
                        for main_limit_id in self.main_limit_identifires[i]:
                            # Определение, содержатся ли основной ограничивающий идентификатор в заданном SKU
                            pos = main_limit_id in sku_row
                            # Если основной ограничивающий идентификатор найден
                            if pos:
                                # Если есть дополнительные ограничивающие идентификаторы
                                if len(self.add_limit_identifires[i]) > 0:
                                    # Перебор дополнительных ограничивающих идентификаторов
                                    for add_limit_id in self.add_limit_identifires[i]:
                                        # Определение, содержатся ли дополнительный ограничивающий идентификатор в заданном SKU
                                        pos = add_limit_id in sku_row
                                        # Если дополнительный ограничивающий идентификатор найден
                                        if pos:
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
                        for excluding_id in self.excluding_identifires[i]:
                            # Определение, содержатся ли исключающий идентификатор в заданном SKU
                            pos = excluding_id in sku_row
                            # Если исключающий идентификатор найден
                            if pos:
                                # Выставляется флаг "исключающий дентификатор найден", цикл поиска исключающих идентификаторов прерывается
                                excluding_id_found = True
                                break
                    # Если "ограничивающие идентификаторы найдены" и не "исключающий дентификатор найден"
                    if limit_id_found and not excluding_id_found:
                        # Возвращается соответствующее обозначение бренда
                        return self.brand_rightholders[i]
        # Если не найдено не одного подходящего бренда, возвращается пустая строка
        return ''

    def identify_brend_and_dec_id(self, sku_row):
        """
        Определение бренда по заданному SKU, а также вывод главного, главного ограничивающего и дополнительного ограничивающего идентификаторов, найденных в SKU и определивших
        предадлежность выбранной категории, если они есть, а иначе пустую строку.
        Заданному SKU соответствует оозначение бренда из brand_rightholders, если он содержит один из основных идентификаторов из соответствующего списка из self.main_identifires,
        один из основных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifires, если он не пустой,
        один из дополнительных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifires, если он не пустой,
        не содержит ни одного из исключающих идентификаторов из self.excluding_identifires.
        Работает аналогично функции identify_brend_and_dec_id, но медленнее

        :param sku_row: SKU, по которому определяется бренд
        :return: обозначение бренда из self.brand_rightholders или пустая строка, если бренд не удается определить; главный решающий идентификатор; главный ограничивающий решающий
        идентификатор; дополнительный ограничивающий решающий идентификатор
        """
        # Перебор всех брендов из справочника
        for i in range(len(self.brand_rightholders)):
            # Перебор основых идентификаторов
            for main_id in self.main_identifires[i]:
                # Определение, содержатся ли основной идентификатор в заданном SKU
                pos = main_id in sku_row
                # Если основной идентификатор найден
                if pos:
                    # Флаг "ограничивающие идентификаторы найдены"
                    limit_id_found = False
                    # Если есть основные ограничивающие идентификаторы
                    if len(self.main_limit_identifires[i]) > 0:
                        # Перебор основных ограничивающих идентификаторов
                        for main_limit_id in self.main_limit_identifires[i]:
                            # Определение, содержатся ли основной ограничивающий идентификатор в заданном SKU
                            pos = main_limit_id in sku_row
                            # Если основной ограничивающий идентификатор найден
                            if pos:
                                # Если есть дополнительные ограничивающие идентификаторы
                                if len(self.add_limit_identifires[i]) > 0:
                                    # Перебор дополнительных ограничивающих идентификаторов
                                    for add_limit_id in self.add_limit_identifires[i]:
                                        # Определение, содержатся ли дополнительный ограничивающий идентификатор в заданном SKU
                                        pos = add_limit_id in sku_row
                                        # Если дополнительный ограничивающий идентификатор найден
                                        if pos:
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
                        for excluding_id in self.excluding_identifires[i]:
                            # Определение, содержатся ли исключающий идентификатор в заданном SKU
                            pos = excluding_id in sku_row
                            # Если исключающий идентификатор найден
                            if pos:
                                # Выставляется флаг "исключающий дентификатор найден", цикл поиска исключающих идентификаторов прерывается
                                excluding_id_found = True
                                break
                    # Если "ограничивающие идентификаторы найдены" и не "исключающий дентификатор найден"
                    if limit_id_found and not excluding_id_found:
                        # Возвращается соответствующее обозначение бренда
                        return self.brand_rightholders[i], main_id, main_limit_dec_id, add_limit_dec_id
        # Если не найдено не одного подходящего бренда, возвращается пустая строка
        return '', '', '', ''
    
    def identify_brend_and_history(self, sku_row):
        """
        
        """
        history = []
        # Перебор всех брендов из справочника
        for i in range(len(self.brand_rightholders)):
            # Перебор основых идентификаторов
            for main_id in self.main_identifires[i]:
                # Определение, содержатся ли основной идентификатор в заданном SKU
                pos = main_id in sku_row
                # Если основной идентификатор найден
                if pos:
                    main_limit_id_found = False
                    # Флаг "ограничивающие идентификаторы найдены"
                    limit_id_found = False
                    # Флаг "исключающий дентификатор найден"
                    excluding_id_found = False
                    # Если есть основные ограничивающие идентификаторы
                    if len(self.main_limit_identifires[i]) > 0:
                        # Перебор основных ограничивающих идентификаторов
                        for main_limit_id in self.main_limit_identifires[i]:
                            # Определение, содержатся ли основной ограничивающий идентификатор в заданном SKU
                            pos = main_limit_id in sku_row
                            # Если основной ограничивающий идентификатор найден
                            if pos:
                                main_limit_id_found = True
                                # Если есть дополнительные ограничивающие идентификаторы
                                if len(self.add_limit_identifires[i]) > 0:
                                    # Перебор дополнительных ограничивающих идентификаторов
                                    for add_limit_id in self.add_limit_identifires[i]:
                                        # Определение, содержатся ли дополнительный ограничивающий идентификатор в заданном SKU
                                        pos = add_limit_id in sku_row
                                        # Если дополнительный ограничивающий идентификатор найден
                                        if pos:
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
                        for excluding_id in self.excluding_identifires[i]:
                            # Определение, содержатся ли исключающий идентификатор в заданном SKU
                            pos = excluding_id in sku_row
                            # Если исключающий идентификатор найден
                            if pos:
                                # Выставляется флаг "исключающий дентификатор найден", цикл поиска исключающих идентификаторов прерывается
                                excluding_id_found = True
                                break
                    history_note = 'Кондидат: \"' + self.brand_rightholders[i] + '\"; Осн. ид.: ' + main_id
                    if len(self.main_limit_identifires[i]) > 0:
                        history_note += '; Осн. огр. ид.: '
                        if main_limit_id_found:
                            history_note += main_limit_id
                        else:
                            history_note += 'не найден'
                        if len(self.add_limit_identifires[i]) > 0:
                            history_note += '; Доп. огр. ид.: '
                            if limit_id_found:
                                history_note += add_limit_id
                            else:
                                history_note += 'не найден'
                    history.append(history_note)
                    if excluding_id_found:
                        history_note += '; Искл. ид.: ' + excluding_id
                    # Если "ограничивающие идентификаторы найдены" и не "исключающий дентификатор найден"
                    if limit_id_found and not excluding_id_found:
                        # Возвращается соответствующее обозначение бренда
                        return self.brand_rightholders[i], '\n'.join(history)
        # Если не найдено не одного подходящего бренда, возвращается пустая строка
        return '', '\n'.join(history)

    def identify_brend_cython(self, sku_row):
        """
        Определение бренда по заданному SKU.
        Заданному SKU соответствует оозначение бренда из brand_rightholders, если он содержит один из основных идентификаторов из соответствующего списка из self.main_identifires,
        один из основных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifires, если он не пустой,
        один из ддополнительных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifires, если он не пустой,
        не содержит ни одного из исключающих идентификаторов из self.excluding_identifires.
        Работает аналогично функции identify_brend, но быстрее засчет использования Cython

        :param sku_row: SKU, по которому определяется бренд
        :return: обозначение бренда из self.brand_rightholders или пустая строка, если бренд не удается определить
        """
        return identify_brend_cython.identify_brend(sku_row, self.brand_rightholders, self.main_identifires, self.main_limit_identifires, self.add_limit_identifires, self.excluding_identifires)

    def identify_brend_and_dec_id_cython(self, sku_row):
        """
        Определение бренда по заданному SKU, а также вывод главного, главного ограничивающего и дополнительного ограничивающего идентификаторов, найденных в SKU и определивших
        предадлежность выбранной категории, если они есть, а иначе пустую строку.
        Заданному SKU соответствует оозначение бренда из brand_rightholders, если он содержит один из основных идентификаторов из соответствующего списка из self.main_identifires,
        один из основных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifires, если он не пустой,
        один из дополнительных ограничивающих идентификаторов из соответствующего списка из self.main_limit_identifires, если он не пустой,
        не содержит ни одного из исключающих идентификаторов из self.excluding_identifires.
        Работает аналогично функции identify_brend_and_dec_id, но быстрее засчет использования Cython

        :param sku_row: SKU, по которому определяется бренд
        :return: обозначение бренда из self.brand_rightholders или пустая строка, если бренд не удается определить
        """
        ret_tuple = identify_brend_cython.identify_brend_and_dec_id(sku_row, self.brand_rightholders, self.main_identifires, self.main_limit_identifires, self.add_limit_identifires, self.excluding_identifires)
        return ret_tuple[0], ret_tuple[1], ret_tuple[2], ret_tuple[3]


    def save(self, dict_name):
        """
        :return: сохраняет этот справочник в директорию saves
        """
        with open(os.path.join('saves', dict_name), 'wb') as file:
            pickle.dump(self, file, protocol=pickle.HIGHEST_PROTOCOL)
