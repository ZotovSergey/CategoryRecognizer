import pandas as pd
import json
import os
import chardet
import re


class SKUReaderCSV:
    """
    Ридер и предобработчик SKU. Читает строки SKU из заданного csv-файла и предобрабатывает их для дальнейшего распозавания категорий
    """
    def __init__(self, data_path, sku_col_name=None, encoding=None):
        """
        :param data_path: путь к читаемому файлу csv, txt содержащему SKU для обработки (str)
        :param sku_col_name: имя столбца файла по пути data_path, содержащему SKU для обработки, если подается пустое название столбца с SKU, то используется первая строка заданного
        файла (str)
        :param encoding: обозначение кодировки, использующейся в csv, txt-файле (str)
        """
        self.data_path = data_path
        self.sku_col = sku_col_name
        # Если подается пустое название столбца с SKU, то используется первая строка заданного файла
        if len(sku_col_name) == 0 or sku_col_name is None:
            self.sku_col = 0
        else:
            self.sku_col = sku_col_name
        self.encoding = encoding
        # Вычисление  длины читаемого файла
        with open(self.data_path, 'r', encoding=encoding) as f:
            for rows_count, line in enumerate(f):
                pass
        self.rows_count = rows_count

    def __len__(self):
        """
        Количество строк читаемого файла
        """
        return self.rows_count
    
    def read(self, start, rows_count):
        """
        Чтение rows_count строк SKU из csv-файла по пути self.data_path, колонки self.rows_col_name с заменой нестандартного символа переноса строки на \n, с кодировкой self.encoding, начиная со строки под
        номером batch_start, не считая заголовка, удаление пустых строк
        
        :param start: номер строки, с которой начинается читаемый батч, не считая заголовка (str)
        :param rows_count: количество строк, читаемых из файла начиная со start (str)

        :return: rows_count строк из файла из csv-файла self.file_path, колонки self.rows_col_name
        """
        return pd.read_csv(self.data_path, usecols=[self.sku_col], skiprows=range(1, start + 1), nrows=rows_count, sep='\t', dtype='str', encoding=self.encoding, skip_blank_lines=False, keep_default_na=False, on_bad_lines='skip').replace(to_replace=r'\r\n', value ='\n', regex=True).dropna().squeeze(axis=1).values.tolist()

    def get_sku_column_name(self):
        """
        :return: название колонки с SKU читаемого файла
        """
        return pd.read_csv(self.data_path, usecols=[self.sku_col], nrows=0, sep='\t', dtype='str', encoding=self.encoding, on_bad_lines='skip').dropna().columns[0]
    
    def get_sku_excel_sheet(self):
        """
        :return: None, так как csv не имеет листа
        """
        return None


class SKUReaderExcel:
    """
    Ридер и предобработчик SKU. Читает строки SKU из заданного  excel-файла и предобрабатывает их для дальнейшего распозавания категорий. Предок класса SKUReader
    """
    def __init__(self, data_path, sku_col_name=None, sku_sheet_name=None):
        """
        :param data_path: путь к читаемому файлу csv, txt, excel, содержащему SKU для обработки (str)
        :param sku_col_name: имя столбца файла по пути data_path, содержащему SKU для обработки; если подается пустое название столбца с SKU, то используется первая строка заданного файла (str)
        :param sku_sheet_name: название листа читаемого excel-файла, содержащего SKU; если подается пустое название листа с SKU, то используется первый лист заданного файла (str)
        """
        # Чтение excel-файла по заданному пути
        ex_file = pd.ExcelFile(data_path)

        # Если подается пустое название читаемого листа excel-файла, то используется первый лист заданного файла
        if len(sku_sheet_name) == 0 or sku_sheet_name is None:
            self.sku_sheet_name = ex_file.sheet_names[0]
        else:
            self.sku_sheet_name = sku_sheet_name
        # Если подается пустое название столбца с SKU, то используется первая строка заданного файла, заданного листа
        if len(sku_col_name) == 0 or sku_col_name is None:
            sku_col = 0
        else:
            sku_col = sku_col_name
        # Строки SKU из заданного файла, заданного листа, заданной строки
        self.data = ex_file.parse(sheet_name=self.sku_sheet_name, usecols=[sku_col], dtype='str', keep_default_na=False, on_bad_lines='skip').dropna()
        
        self.column_name = self.data.columns[0]

        self.data = self.data.squeeze(axis=1).values.tolist()
    
    def __len__(self):
        """
        Количество строк читаемого файла
        """
        return len(self.data)

    def read(self, start, rows_count):
        """
        Чтение rows_count строк SKU из self.data, начиная со строки под номером batch_start, не считая заголовка

        :param start: номер строки, с которой начинается читаемый батч, не считая заголовка (str)
        :param rows_count: количество строк, читаемых из файла начиная со start (str)

        :return: self.batch_len строк из excel-файла self.file_path, листа self.sheet_name, колонки self.rows_col_name
        """
        return self.data[start : start + rows_count]
    
    def get_sku_column_name(self):
        """
        :return: название столбца с SKU читаемого файла
        """
        return self.column_name
    
    def get_sku_excel_sheet(self):
        """
        :return: название листа с SKU читаемого файла
        """
        return self.sku_sheet_name

"""
Райтер для записи данных в CSV файл

:param file_path: путь к записываемому файлу
:param encoding: кодировка записываемого файла
"""

def init_writer(file_path):
    writer = SKUWriterCSV(file_path)
    writer.encoding = None
    return writer

class SKUWriterCSV:
    def __init__(self, file_path):
        self.file_path = file_path

    def write(self, df):
        df.to_csv(self.file_path, sep='\t', index=False, encoding=self.encoding, errors="ignore")
    
    def append(self, df):
        df.to_csv(self.file_path, sep='\t', index=False, header=False, mode='a', encoding=self.encoding, errors="ignore")

def init_sku_reader(data_path, sku_sheet_name=None, sku_col_name=None):
    """
    Создание ридера (объекта, содержащий функцию read(batch_start, batch_len), считывающий batch_len строк SKU начиная с batch_start) и предобработчика батчей SKU из csv, txt или excel-файла, в зависимости от расширения файла

    :param file_path: путь к читаемому файлу содержащему SKU для обработки (str)
    :param sku_sheet_name: название листа читаемого excel-файла, содержащего SKU (если данные читаются из excel-файла); если подается пустое название столбца с SKU, то используется первая строка заданного файла (str)
    :param sku_col_name: имя столбца файла по пути data_path, содержащему SKU для обработки; если подается пустое название листа с SKU, то используется первый лист заданного файла (str)

    :return: ридер и предобработчик батчей SKU из csv, txt или excel-файла, в зависимости от расширени файла (SKUReaderCSV или SKUReaderExcel)
    """
    #   Определение расширения файла
    file_ext = data_path.split('.')[-1]
    #   Определение типа обрабатываемого файла и определение необходимых для полученного типа параметров
    if  file_ext in json.load(open(os.path.join('config', 'file_ext.json')))['excel_ext']:
        # Формат обрабатываемого файла - excel
        # Создание объекта-ридера SKU из excel-файла по пути input_data_path, из листа sku_sheet_name (или первого листа), из столбца sku_col_name (или первого столбца),
        # осуществляющего чтение и предобработку SKU
        sku_reader = SKUReaderExcel(data_path, sku_col_name, sku_sheet_name)
        # Заполнение пустого значения названия листа с SKU excel-файла
        if len(sku_sheet_name) == 0:
            sku_sheet_name = sku_reader.sku_sheet_name
    else:
        # Формат обрабатываемого файла - csv, txt
        # Определение кодировки обрабатываемого файла
        #   Сообщение о начале определния кодировки
        bytesArr = open(data_path, 'rb').read(1000000)
        encoding = chardet.detect(bytesArr)['encoding']
        # Создание объекта-ридера SKU из csv-файла по пути input_data_path, из столбца sku_col_name (или первого столбца), осуществляющего чтение и предобработку SKU
        sku_reader = SKUReaderCSV(data_path, sku_col_name, encoding)
    return sku_reader

def preprocess_sku_for_recognizing(sku):
    """
    Предобработка SKU для распознования категории

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return add_spaces_at_start_end(sku.upper())

def base_cleanning(sku):
    """
    Общая очистка SKU от лишней информации, характерной для любых случаев и приведенеи к более общему виду

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    # Замена всех нестандартных пробельных символов на обычные пробелы
    cleared_sku = replace_bad_spaces(sku)
    # Замена всех скобок на обычные
    cleared_sku = replace_brackets(cleared_sku)
    # Замена обратных слэшей на обычные и их сжатие
    cleared_sku = replace_backslashes(cleared_sku)
    # Ряд трансформация идут по тех пор, пока не прекратятся изменения строки
    start_is_clear = False
    while not start_is_clear:
        # Удаление ряда символов перед двоеточием в начале строки
        new_cleared_sku = remove_eight_symb_before_colon_at_start(cleared_sku)
        # Удаление набора символов кроме знака "<" из начала строки
        new_cleared_sku = remove_symb2_ex_less_at_start(new_cleared_sku)
        # Удаление некоторых символов из начала строки
        new_cleared_sku = remove_symb1_at_start(new_cleared_sku)
        # Удаление записей в скобках <> из начала строки
        new_cleared_sku = remove_note_between_angle_brackets_at_start(new_cleared_sku)
        # Удаление знака "<" из начала строки
        new_cleared_sku = remove_less_at_start(new_cleared_sku)
        # Удаление записей (М) и (М+) в начале SKU
        new_cleared_sku = remove_m_symb_at_start(new_cleared_sku)
        # Сжатие пробелов
        new_cleared_sku = squeeze_spaces(new_cleared_sku)
        # Проверка изменения в строке
        if cleared_sku == new_cleared_sku:
            start_is_clear = True
        cleared_sku = new_cleared_sku
    # Замена некоторых символов строки на пробелы
    cleared_sku = replace_symb2_all(cleared_sku)
    # Замена сочетаний более одного "*" через пробелы на пробел
    cleared_sku = replace_many_asteriskes(cleared_sku)
    # Замена сочетаний более одного "!" на пробел
    cleared_sku = replace_many_exclamation_points(cleared_sku)
    # Замена сочетаний более одного "$" на пробел
    cleared_sku = replace_many_dollars(cleared_sku)
    # Замена сочетаний более одного "+" на пробел
    cleared_sku = replace_many_pluses(cleared_sku)
    # Замена сочетаний более одного "/" на пробел
    cleared_sku = replace_many_slashes(cleared_sku)
    # Замена сочетаний более одного ";" на пробел
    cleared_sku = replace_many_semicolon(cleared_sku)
    # Замена сочетаний более одного "_" на пробел
    cleared_sku = replace_many_underscore(cleared_sku)
    # Ряд трансформация идут по тех пор, пока не прекратятся изменения строки
    start_is_clear = False
    while not start_is_clear:
        # Удаление обозначения "КНОПКА" в конце строки
        new_cleared_sku = remove_buton_note_at_end(cleared_sku)
        # Удаление цифр после двоеточия в конце
        new_cleared_sku = remove_num_symb_after_colon_at_end(new_cleared_sku)
        # Сжатие пробелов
        new_cleared_sku = squeeze_spaces(new_cleared_sku)
        # Проверка изменения в строке
        if cleared_sku == new_cleared_sku:
            start_is_clear = True
        cleared_sku = new_cleared_sku
    # Удаление пробелов в начале и в конце
    cleared_sku = remove_spaces_at_start_end(cleared_sku)

    return cleared_sku

def add_spaces_at_start_end(sku):
    """
    Добавление пробелов в начало и конец строки

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return "".join([' ', sku, ' '])

def replace_bad_spaces(sku):
    """
    Замена пробела с кодировкой \u00a0 на обычный

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'[\s\u00a0\u0009\u000b\u000a]', ' ', sku)

def squeeze_spaces(sku):
    """
    Замена множественных пробелов на одинарные (сжимание пробелов)

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'\s{2,}', ' ', sku)

def remove_eight_symb_before_colon_at_start(sku):
    """
    Удаление символов левее двоеточие, если двоеточие не более, чем на восьмой позиции слева
    
    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'^.{0,7}:', '', sku)

def remove_symb1_at_start(sku):
    """
    Удаление символов " ", ".", ",", "_", "-", "–", "*", "!", "^", "=", "$", "@", "+", "/" в начале SKU на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'^\s*[\.\,_\-–\*\!\^\=\$@\+\/]+', '', sku)

def remove_note_between_angle_brackets_at_start(sku):
    """
    Удаление символов записи между скобками "<", ">" в начале SKU

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'^\s*<.{0,}>', '', sku)

def remove_m_symb_at_start(sku):
    """
    Удаление записей (М) и (М+) в начале SKU

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'^\s*\([MМ]\+?\)', '', sku)

def replace_symb2_all(sku):
    """
    Замена символов "~", "«", "»", "“", "”", "\"", "\'", "`", "#", "?", "<", ">", "‘", "∙" и множество других символов на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'[~«»“”\"\'`#?<>‘∙\u2524\u2561\u2556\u2555\u2563\u2551\u2557\u255d\u255c\u255b\u2510\u2514\u2534\u252c\u251c\u2500\u253c\u255e\u255f\u255a\u2554\u2569\u2566\u2560\u2550\u256c\u2567\u2568\u2564\u2565\u2559\u2558\u2552\u2553\u256b\u256a\u2518\u250c\u2588\u2584\u258c\u2590\u2580]', ' ', sku)

def remove_symb2_ex_less_at_start(sku):
    """
    Удаление символов "~", "«", "»", "“", "”", "\"", "\'", "`", "#", "?", ">", "‘", "∙" и множество других символов

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'^\s*[~«»“”\"\'`#?>‘∙\u2524\u2561\u2556\u2555\u2563\u2551\u2557\u255d\u255c\u255b\u2510\u2514\u2534\u252c\u251c\u2500\u253c\u255e\u255f\u255a\u2554\u2569\u2566\u2560\u2550\u256c\u2567\u2568\u2564\u2565\u2559\u2558\u2552\u2553\u256b\u256a\u2518\u250c\u2588\u2584\u258c\u2590\u2580]+', '', sku)

def remove_less_at_start(sku):
    """
    Удаление символа "<"

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'^\s*[<]+', '', sku)

def replace_less_at_start(sku):
    """
    Замена символов "~", "«", "»", "“", "”", "\"", "\'", "`", "#", "?", ">", "‘", "∙" и множество других символов на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'[~«»“”\"\'`#?>‘∙\u2524\u2561\u2556\u2555\u2563\u2551\u2557\u255d\u255c\u255b\u2510\u2514\u2534\u252c\u251c\u2500\u253c\u255e\u255f\u255a\u2554\u2569\u2566\u2560\u2550\u256c\u2567\u2568\u2564\u2565\u2559\u2558\u2552\u2553\u256b\u256a\u2518\u250c\u2588\u2584\u258c\u2590\u2580]', ' ', sku)

def replace_many_asteriskes(sku):
    """
    Замена сочетаний более одного "*" на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'\*+\s*\*+[\s\*]*', ' ', sku)

def replace_many_exclamation_points(sku):
    """
    Замена сочетаний более одного "!" на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'\!+\s*\!+[\s\!]*', ' ', sku)

def replace_many_dollars(sku):
    """
    Замена сочетаний более одного "$" на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'\$+\s*\$+[\s\$]*', ' ', sku)

def replace_many_pluses(sku):
    """
    Замена сочетаний более одного "+" на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'\++\s*\++[\s\+]*', ' ', sku)

def replace_many_slashes(sku):
    """
    Замена сочетаний более одного "/" на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'/+\s*/+[\s/]*', ' ', sku)

def replace_many_semicolon(sku):
    """
    Замена сочетаний более одного ";" на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r';+\s*;+[\s;]*', ' ', sku)

def replace_many_underscore(sku):
    """
    Замена сочетаний более одного "_" на пробел

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'_+\s*_+[\s_]*', ' ', sku)

def replace_brackets(sku):
    """
    Замена квадратных и фигурных на круглые

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'[}\]]', ')', re.sub(r'[{\[]', '(', sku))

def replace_backslashes(sku):
    """
    Замена символов обратных слэшей на обычные и сжимание обычных слэшей

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'\\', '/', sku)

def remove_num_symb_after_colon_at_end(sku):
    """
    Удаление всех цифровых символов (а таке пробелов, слэшей) после двоеточия в конце строки

    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r':[0-9/\s.,]{0,}$', '', sku)

def remove_buton_note_at_end(sku):
    """
    Удаление записи "КНОПКА" и цифры с дефисом в конце SKU
    
    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'КНОПКА[0-9-\s]{0,}$', '', sku)

def remove_spaces_at_start_end(sku):
    """
    Удаление пробелов в начале и в конце
    
    :param sku: строка SKU (string)

    :return: измененная строка SKU
    """
    return re.sub(r'\s$', '', re.sub(r'^\s', '', sku))

def remove_numbers_under_value(sku, value):
    """
    Удаление чисел больше value
    
    :param sku: строка SKU (string)
    :param value: значение, числа выше которого необходимо удалять из SKU (int)

    :return: измененная строка SKU
    """
    # Все числа в SKU
    numbers_list = re.findall(r'[0-9]+[.,]?[0-9]*', sku)
    # Перебор всех чисел
    for num_str in numbers_list:
        # Проверка значения числа
        if float(num_str.replace(",", ".")) > value:
            sku = sku.replace(num_str, " ")
    return sku

CLEAR_PATTERNS_DICT = {
                      'Базовый': base_cleanning
                      }

