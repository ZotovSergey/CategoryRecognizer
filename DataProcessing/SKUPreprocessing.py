import pandas as pd
import csv

# def clear_sku(sku_rows):
#     cleaned_sku_rows = sku_rows.str.replace(r'\s{2,}', ' ')
#     cleaned_sku_rows = cleaned_sku_rows.str.replace.str.replace(r'^\[[^\[\]]*\]|^{[^{}]*}|^<[^<>]*>|~|^#|^\'|^\?|^\*|^\.|^\,|^_|^-|^–|{|}', '')
#     return cleaned_sku_rows

def preprocess_sku_df(sku_df):
    """
    Предобработка SKU для распознования категории
    """
    sku_rows = sku_df.squeeze()
    # Приведение SKU к верхнему регистру и расставление пробелов в начале и в конце строк
    preprocessed_rows = list(' ' + sku_rows.str.upper() + ' ')
    return preprocessed_rows, sku_rows


class SKUReaderCSV:
    """
    Ридер и предобработчик SKU. Читает строки SKU из заданного csv-файла и предобрабатывает их для дальнейшего распозавания категорий
    """
    def __init__(self, data_path, sku_col_name, encoding):
        """
        :param data_path: путь к читаемому файлу csv, txt, excel, содержащему SKU для обработки (str)
        :param sku_col_name: имя столбца файла по пути data_path, содержащему SKU для обработки (str)
        :param encoding: обозначение кодировки, использующейся в csv, txt-файле (str)
        """
        self.data_path = data_path
        self.sku_col = sku_col_name
        # Если подается пустое название столбца с SKU, то используется первая строка заданного файла, заданного листа
        if len(sku_col_name) == 0 or sku_col_name is None:
            self.sku_col = 0
        else:
            self.sku_col = sku_col_name
        self.encoding = encoding

    def __len__(self):
        """
        Количество строк читаемого файла
        """
        rows_count = -1
        for line in csv.reader(open(self.data_path, 'r', encoding=self.encoding)):
            rows_count += 1
        return rows_count
    
    def read(self, start, rows_count):
        """
        Чтение rows_count строк SKU из csv-файла по пути self.data_path, колонки self.rows_col_name, с кодировкой self.encoding, начиная со строки под номером batch_start, не считая заголовка и предобработка для
        дальнейшего распознование категорий
        
        :param start: номер строки, с которой начинается читаемый батч, не считая заголовка (str)
        :param rows_count: количество строк, читаемых из файла начиная со start (str)

        :return: self.batch_len строк из файла из csv-файла self.file_path, колонки self.rows_col_name
        """
        return preprocess_sku_df(pd.read_csv(self.data_path, header=None, usecols=[self.sku_col], skiprows=start + 1, nrows=rows_count, sep='\t', dtype='str', encoding=self.encoding).fillna(''))

    def column_name(self):
        """
        :return: название колонки с SKU читаемого файла
        """
        return pd.read_csv(self.data_path, header=None, usecols=[self.sku_col], nrows=1, sep='\t', dtype='str', encoding=self.encoding).fillna('')[0][0]


class SKUReaderExcel:
    """
    Ридер и предобработчик SKU. Читает строки SKU из заданного  excel-файла и предобрабатывает их для дальнейшего распозавания категорий. Предок класса SKUReader
    """
    def __init__(self, data_path, sku_col_name=None, sku_sheet_name=None):
        """
        :param data_path: путь к читаемому файлу csv, txt, excel, содержащему SKU для обработки (str)
        :param sku_col_name: имя столбца файла по пути data_path, содержащему SKU для обработки (str)
        :param sku_sheet_name: название листа читаемого excel-файла, содержащего SKU (str)
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
        # Строк SKU из заданного файла, заданного листа, заданной строки
        self.data = ex_file.parse(sheet_name=self.sku_sheet_name, usecols=[sku_col], dtype='str').fillna('')
    
    def __len__(self):
        """
        Количество строк читаемого файла
        """
        return len(self.data)

    def read(self, start, rows_count):
        """
        Чтение rows_count строк SKU из self.data, начиная со строки под номером batch_start, не считая заголовка и предобработка для дальнейшего распознование категорий

        :param start: номер строки, с которой начинается читаемый батч, не считая заголовка (str)
        :param rows_count: количество строк, читаемых из файла начиная со start (str)

        :return: self.batch_len строк из excel-файла self.file_path, листа self.sheet_name, колонки self.rows_col_name
        """
        return preprocess_sku_df(self.data[start : start + rows_count])
    
    def column_name(self):
        """
        :return: название колонки с SKU читаемого файла
        """
        return self.data.columns[0]