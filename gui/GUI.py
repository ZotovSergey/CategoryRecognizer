import sys
import os
import pandas as pd
import json

import chardet

from math import floor

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator, QIcon

import multiprocessing as mp
from datetime import datetime

from DataProcessing.DataProcessing import BrendRecognizer
from DataProcessing.SKUPreprocessing import SKUReaderCSV, SKUReaderExcel
from BrendDictionary.BrendDictionary import BrendDictionary, find_all_dict, load_dictionary


class Window(QWidget):
    """
    Окно приложения, содержит размеры и разметку
    """
    def __init__(self):
        super().__init__()
        # Ширина окна
        self.window_wight = 600
        # Высота окна
        self.window_high = 600
        # Отступ от края окна по горизонтали
        self.margin_hor = 10
        # Отступ от края окна по вертикали
        self.margin_vert = 10
        # Отступ от подписи по вертикали
        self.space_after_label_vert = 15
        # Пространство между элементами
        self.space = 10
        # Ширина кнопки вызова окна выбора файла
        self.file_path_btn_wight = 30
        # Высота кнопки вызова окна выбора файла
        self.file_path_btn_high = 25
        # Высота строки ввода
        self.input_line_high = 25
        # Ширина длинной строки ввода
        self.input_line_wight = int(self.window_wight - 2 * self.margin_vert - self.file_path_btn_wight - self.space)
        # Доступная ширина окна
        self.content_wight = self.window_wight - 2 * self.margin_hor
        # Ширина короткой строки ввода
        self.short_input_line_wight = 100
        # Отступ для второго столбца по горизонтали
        self.second_col_hor = int(self.window_wight / 2)
        # Фиксация размера окна
        self.setFixedSize(self.window_wight, self.window_high)
        # Название окна
        self.setWindowTitle('Category Recognizer')

    def get_path_from_file_dialog(self, dialog_name, existed=True):
        """
        Выбор файла в диалоговом окне
        :param dialog_name: название диалогового окна (str)
        :param existed: выбиремый файл должен существовать (bool)
        
        :return: путь к выбранному файлу (существующему или не существующему)
        """
        # Путь к директории, в которой открывается диалоговое окно
        initial_dir = os.path.join(os.path.splitdrive(os.path.abspath(__file__))[0], os.sep)
        # Выбор вида открываемого диалогового окна: для загрузки существующего файла или сохранения файла
        if existed:
            return QFileDialog.getOpenFileName(self, dialog_name, initial_dir)[0]
        else:
            return QFileDialog.getSaveFileName(self, dialog_name, initial_dir)[0]
    
    def set_message(self, msg):
        """
        Записывает заданное сообщение msg в текстовое окно интерфейса self.dict_sheet_name_line_edit
        :param msg: строка сообщения (str)
        :return: записывает msg в окно сообщений
        """
        self.proc_progress_text.append(msg)
        QApplication.processEvents()

    def countdown(self):
        """
        Вывод отсчета времени от заданного начала отчета времени self.proc_begin_time в формате строки 'h:mm:ss'
        :return: Отсчет времени от заданного начала отчета времени self.proc_begin_time в формате строки 'h:mm:ss'
        """
        # Вычисление времени от начала отсчета self.proc_begin_time
        time = datetime.now() - self.proc_begin_time
        # Вычисление целых часов, минут и секунд в time
        hours, reminder = divmod(time.total_seconds(), 60)
        minutes, seconds = divmod(reminder, 60)
        hours_str = str(floor(hours))
        minutes_str = str(floor(minutes))
        # Приведение целых минут и секунд к формату mm и ss, соответственно
        if len(minutes_str) == 1:
            minutes_str = '0' + minutes_str
        seconds_str = str(floor(seconds))
        if len(seconds_str) == 1:
            seconds_str = '0' + seconds_str
        # Вывод времени в формате h:mm:ss
        return ":".join([hours_str, minutes_str, seconds_str])

class ProcessingWindow(Window):
    """
    Окно обработки данных
    """
    def __init__(self):
        super().__init__()
        
        # Максимальное число потоков
        self.cpu_max = mp.cpu_count()
        # Максимальная длина батча по умолчанию
        self.default_max_batch_len = 100000
        # Создание окна
        self.initUI()

    def initUI(self):
        """
        Создание окна
        """
        # Положение следующей строки по вертикали
        new_line_vert = self.margin_vert

        # Выбор справочника
        #   Подпись
        self.select_dict_label = QLabel(self)
        self.select_dict_label.setText('Справочник:')
        self.select_dict_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Комбо бокс
        self.select_dict_combo = QComboBox(self)
        self.select_dict_combo.move(self.margin_hor, new_line_vert)
        self.select_dict_combo.resize(self.input_line_wight, self.input_line_high)
        self.find_dictionaries()
        new_line_vert += self.input_line_high + self.space

        # Ввод пути к обрабатываемому файлу
        #   Подпись
        self.input_file_path_label = QLabel(self)
        self.input_file_path_label.setText('Путь к обрабатываемому файлу:')
        self.input_file_path_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.input_file_path_line_edit = QLineEdit(self)
        self.input_file_path_line_edit.move(self.margin_hor, new_line_vert)
        self.input_file_path_line_edit.resize(self.input_line_wight, self.input_line_high)
        #   Кнопка вызова диалогового окна выбора файла
        self.input_file_path_btn = QPushButton('...', self)
        self.input_file_path_btn.move(self.input_line_wight + self.margin_vert + self.space, new_line_vert)
        self.input_file_path_btn.resize(self.file_path_btn_wight, self.file_path_btn_high)
        self.input_file_path_btn.clicked.connect(self.input_file_path_btn_click)
        new_line_vert += self.input_line_high + self.space

        # Ввод названия страницы SKU в обрабатываемом excel-файле
        #   Подпись
        self.sku_sheet_name_label = QLabel(self)
        self.sku_sheet_name_label.setText('Название страницы SKU в обрабатываемом файле (если файл excel):')
        self.sku_sheet_name_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.sku_sheet_name_line_edit = QLineEdit(self)
        self.sku_sheet_name_line_edit.move(self.margin_hor, new_line_vert)
        self.sku_sheet_name_line_edit.resize(self.input_line_wight, self.input_line_high)
        new_line_vert += self.input_line_high + self.space

        # Ввод названия столбца SKU в обрабатываемом файле
        #   Подпись
        self.sku_col_name_label = QLabel(self)
        self.sku_col_name_label.setText('Название столбца SKU в обрабатываемом файле:')
        self.sku_col_name_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.sku_col_name_text_edit = QTextEdit(self)
        self.sku_col_name_text_edit.move(self.margin_hor, new_line_vert)
        self.sku_col_name_text_edit.resize(self.input_line_wight, self.input_line_high)
        new_line_vert += self.input_line_high + self.space

        # Ввод пути к исходящему файлу
        #   Подпись
        self.output_file_path_label = QLabel(self)
        self.output_file_path_label.setText('Путь к исходящему файлу:')
        self.output_file_path_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.output_file_path_line_edit = QLineEdit(self)
        self.output_file_path_line_edit.move(self.margin_hor, new_line_vert)
        self.output_file_path_line_edit.resize(self.input_line_wight, self.input_line_high)
        #   Кнопка вызова диалогового окна выбора файла
        self.output_file_path_btn = QPushButton('...', self)
        self.output_file_path_btn.move(self.input_line_wight + self.margin_vert + self.space, new_line_vert)
        self.output_file_path_btn.resize(self.file_path_btn_wight, self.file_path_btn_high)
        self.output_file_path_btn.clicked.connect(self.output_file_path_btn_click)
        new_line_vert += self.input_line_high + self.space

        # Чебокс вывода идентификаторов
        self.id_output_check = QCheckBox("Выводить соответствующие идентифиаторы", self)
        self.id_output_check.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert + self.space
        
        # Блок параметров вычислений
        #   Подпись
        self.calc_param_block_label = QLabel(self)
        self.calc_param_block_label.setText('Параметры вычислений')
        self.calc_param_block_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Ввод количества потоков, использующихся при вычислениях
        #       Подпись
        self.use_threads_count_label = QLabel(self)
        self.use_threads_count_label.setText('Кол-во задействованных потоков:')
        self.use_threads_count_label.move(self.margin_hor, new_line_vert)
        #   Ввод количества строк в батче
        #       Подпись
        self.use_threads_count_label = QLabel(self)
        self.use_threads_count_label.setText('Макс. кол-во строк в батче:')
        self.use_threads_count_label.move(self.second_col_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Ввод количества потоков, использующихся при вычислениях
        #       Строка ввода
        self.use_threads_count_line_edit = QLineEdit(self)
        self.use_threads_count_line_edit.move(self.margin_hor, new_line_vert)
        self.use_threads_count_line_edit.resize(self.short_input_line_wight, self.input_line_high)
        self.use_threads_count_line_edit.setValidator(QIntValidator())
        #       Ввод максимального кол-ва ядер, как значения по умолчанию
        self.max_threads_btn_click()
        #       Кнопка ввода максимального кол-ва потоков для вычисления
        self.max_threads_btn = QPushButton('MAX', self)
        self.max_threads_btn.resize(self.max_threads_btn.sizeHint())
        self.max_threads_btn.move(self.margin_hor + self.short_input_line_wight + self.space, new_line_vert)
        self.max_threads_btn.clicked.connect(self.max_threads_btn_click)

        #   Ввод количества строк в батче
        #       Строка ввода
        self.max_batch_len_line_edit = QLineEdit(self)
        self.max_batch_len_line_edit.move(self.second_col_hor, new_line_vert)
        self.max_batch_len_line_edit.resize(self.short_input_line_wight, self.input_line_high)
        self.max_batch_len_line_edit.setValidator(QIntValidator())
        self.max_batch_len_line_edit.setText(str(self.default_max_batch_len))
        new_line_vert += self.input_line_high + self.space

        # Кнопка запуска вычислений
        self.run_btn = QPushButton('ЗАПУСК', self)
        self.run_btn.resize(self.run_btn.sizeHint())
        self.run_btn.move(self.window_wight - self.run_btn.size().width() - self.margin_hor, self.window_high - self.run_btn.size().height() - self.margin_vert)
        self.run_btn.clicked.connect(self.run)

        # Отображение хода вычислений
        #   Подпись
        self.proc_progress_label = QLabel(self)
        self.proc_progress_label.setText('Ход обработки:')
        self.proc_progress_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Текстовое окно
        msg_window_high = self.window_high - 2 * self.margin_vert - self.run_btn.size().height() - new_line_vert - self.input_line_high - self.space - self.space_after_label_vert
        self.proc_progress_text = QTextEdit(self)
        self.proc_progress_text.move(self.margin_hor, new_line_vert)
        self.proc_progress_text.resize(self.content_wight, msg_window_high)
        self.proc_progress_text.setReadOnly(True)
        new_line_vert += msg_window_high + self.space

        # Отображение progress bar обработки
        #   Подпись
        self.pbar_label = QLabel(self)
        self.pbar_label.setText('Прогресс обработки:')
        self.pbar_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Progress bar
        self.pbar = QProgressBar(self)
        self.pbar.move(self.margin_hor, new_line_vert)
        self.pbar.resize(self.content_wight, self.input_line_high)
        #       Обнуление progress bar
        self.pbar.setValue(0)
        #   Заполнение редактирумых элементов окна значениями из конфигурационного файла, которыми эти элементы были заполнены при последнем успешном запуске вычислений
        self.load_config()

    def input_file_path_btn_click(self):
        """
        Функция кнопки вызова диалогового окна выбора файла для строки ввода обрабатываемого файла
        :return: в строку ввода обрабатываемого файла вводится путь к выбраному файлу
        """
        choosed_file_path = self.get_path_from_file_dialog('Обрабатываемый файл')
        if choosed_file_path != '':
            self.input_file_path_line_edit.setText(choosed_file_path)

    def output_file_path_btn_click(self):
        """
        Функция кнопки вызова диалогового окна выбора файла для строки ввода исходящеего файла
        :return: в строку ввода исходящего файла вводится путь к выбраному файлу
        """
        choosed_file_path = self.get_path_from_file_dialog('Исходящий файл', existed=False)
        if choosed_file_path != '':
            self.output_file_path_line_edit.setText(choosed_file_path)

    def max_threads_btn_click(self):
        """
        Функция кнопки ввода максимального кол-ва потоков для вычисления
        :return: записывает в строку ввода используемого количества потоков максималього числа потоков
        """
        self.use_threads_count_line_edit.setText(str(self.cpu_max))
    
    def find_dictionaries(self):
        """
        Находит названия доступных справочников и добавляет их в комбобокс выбора справочника
        :return: добавляет названия доступных справочников в комбобокс выбора справочника
        """
        self.select_dict_combo.clear()
        dict_list = find_all_dict()
        self.select_dict_combo.addItems(dict_list)
    
    def save_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых элементов окна вычислений, которые будут воспроизводиться при открытии окна в следущую сессию
        :return: файл json, содержащий значения редактируемых элементов окна вычислений
        """
        dict_win_config = {
                           'sel_dict': self.select_dict_combo.currentText(),
                           'input_data_path': self.input_file_path_line_edit.text(),
                           'sku_sheet_name': self.sku_sheet_name_line_edit.text(),
                           'sku_col_name': self.sku_col_name_text_edit.toPlainText(),
                           'output_data_path': self.output_file_path_line_edit.text(),
                           'use_threads_count': self.use_threads_count_line_edit.text(),
                           'max_batch_len': self.max_batch_len_line_edit.text(),
                           'dec_id': self.id_output_check.isChecked()
                          }
        with open(os.path.join('config', 'proc_win_config.json'), 'w') as config_file:
            config_file.write(json.dumps(dict_win_config))

    def load_config(self):
        """
        Заполнение редактируемых элементов окна составления словаря значениями из сохраненного конфигурационного файла config\\proc_win_config.json, если он есть
        """
        try:
            with open(os.path.join('config', 'proc_win_config.json')) as config_file:
                dict_win_config = json.load(config_file)
            self.select_dict_combo.setCurrentText(dict_win_config['sel_dict'])
            self.input_file_path_line_edit.setText(dict_win_config['input_data_path'])
            self.sku_col_name_text_edit.setText(dict_win_config['sku_col_name'])
            self.output_file_path_line_edit.setText(dict_win_config['output_data_path'])
            self.use_threads_count_line_edit.setText(dict_win_config['use_threads_count'])
            self.max_batch_len_line_edit.setText(dict_win_config['max_batch_len'])
            self.id_output_check.setChecked(dict_win_config['dec_id'])
            self.sku_sheet_name_line_edit.setText(dict_win_config['sku_sheet_name'])
        except:
            print()
    
    def run(self):
        try:
            # Обнуление progress bar
            self.pbar.setValue(0)
            # Начало отсчета таймера
            self.proc_begin_time = datetime.now()
            # Сбор данных из GUI и определение параметров файла с данными для обработки, подготовка к началу рассчетов
            #   Загрузка выбранного справочника, по нему будет идти распознавание категорий
            sel_dict = load_dictionary(self.select_dict_combo.currentText())
            #   Сообщение о завершении загрузки справочника
            self.set_message(self.countdown() + '\tСправочник \"' + self.select_dict_combo.currentText() + '\" загружен')
            #   Путь к csv файлу, со строками SKU для обработки
            input_data_path = self.input_file_path_line_edit.text()
            #   Кодировка файла с данными
            encoding = None
            #   Страница excel-файла, содержащей строки SKU для обработки
            sku_sheet_name = None
            #   Определение расширения файла
            file_ext = input_data_path.split('.')[-1]
            #   Название столбца, содержащего строки SKU для обработки, если строка пустая, то берется первый столбец в заданном файле
            sku_col_name = self.sku_col_name_text_edit.toPlainText()
            #   Определение типа обрабатываемого файла и определение необходимых для полученного типа параметров
            if  file_ext in json.load(open(os.path.join('config', 'excel_ext.json')))['excel_ext']:
                # Формат обрабатываемого файла - excel
                # Название страницы, содержащей строки SKU для обработки, если строка пустая, то берется первая страница в заданном файле
                sku_sheet_name = self.sku_sheet_name_line_edit.text()
                # Создание объекта-ридера SKU из excel-файла по пути input_data_path, из страницы sku_sheet_name (или первой страницы), из столбца sku_col_name (или первого столбца),
                # осуществляющего чтение и предобработку SKU
                sku_reader = SKUReaderExcel(input_data_path, sku_col_name, sku_sheet_name)
                # Заполнение пустого значения названия страницы с SKU excel-файла
                if len(sku_sheet_name) == 0:
                    sku_sheet_name = sku_reader.sku_sheet_name
            else:
                # Формат обрабатываемого файла - csv, txt
                # Определение кодировки обрабатываемого файла
                #   Сообщение о начале определния кодировки
                self.set_message(self.countdown() + '\tОпределение кодировки обрабатываемого файла')
                encoding = chardet.detect(open(input_data_path, 'rb').read())['encoding']
                #   Сообщение о определенной кодировки
                self.set_message(self.countdown() + '\tКодировка обрабатываемого файла:\t\"' + encoding + '\"')
                # Создание объекта-ридера SKU из csv-файла по пути input_data_path, из столбца sku_col_name (или первого столбца), осуществляющего чтение и предобработку SKU
                sku_reader = SKUReaderCSV(input_data_path, sku_col_name, encoding)
            #   Заполнение пустого значения названия столбца с SKU
            if len(sku_col_name) == 0:
                sku_col_name = sku_reader.column_name()
            #   Путь к файлу, в который будут выводиться результаты распознавания
            output_data_path = self.output_file_path_line_edit.text()
            #   Количество задействованых в вычислении потоков, если строка пустая, то берется максимальное доступное количество потоков
            use_threads_count = self.use_threads_count_line_edit.text()
            if len(use_threads_count) == 0:
                use_threads_count == self.cpu_max
                # Заполнение пустой строки значением по умолчанию
                self.use_threads_count_line_edit.setText(str(use_threads_count))
            else:
                use_threads_count = int(use_threads_count)
            #   Максимальное количество строк в одном батче, если строка пустая, то берется значение потоков по умолчанию
            max_batch_len = self.max_batch_len_line_edit.text()
            if len(max_batch_len) == 0:
                max_batch_len == self.default_max_batch_len
                # Заполнение пустой строки значением по умолчанию
                self.max_batch_len_line_edit.setText(str(use_threads_count))
            else:
                max_batch_len = int(max_batch_len)
            
            # Обработка
            #   Сообщение о начале обработки
            #   Добавочное сообщение о том, что выводятся определяющие идентификаторы
            if self.id_output_check.isChecked():
                id_output_add_msg = ' с выводом определяющих идентификаторов'
            else:
                id_output_add_msg = ''
            self.set_message(self.countdown() + '\tРаспознование категорий по SKU' + id_output_add_msg)
            self.set_message('\tиз файла \"' + input_data_path + '\";')
            self.set_message('\tстолбец SKU:\t\t\t\"' + sku_col_name + '\";')
            self.set_message('\tкол-во задействованных потоков:\t' + str(use_threads_count) + ';')
            self.set_message('\tмакс. кол-во строк в батче:\t\t' + str(max_batch_len) + ';')
            self.set_message('\tрезультат обработки будет сохранен в файл:\t\"' + output_data_path + '\"')
            #   Создание объекта, распознающего категории по SKU в соответствии справочнику sel_dict
            br = BrendRecognizer(sku_reader, sel_dict, max_batch_len=max_batch_len, get_dec_id=self.id_output_check.isChecked(), cpu_count=use_threads_count)
            #   Распознавание SKU из заданного файла в соответствии заданному справочнику
            br.process_data(output_data_path, gui_window=self)
            #   Сообщение о завершении обработки
            self.set_message(self.countdown() + '\tРаспознвание категорий по SKU завершено, результаты сохранены в исходящий файл')
            #   Запись содержания строк окна в конфигурационный файл json, в следующую сессию эти строки записываются при открытии окна
            self.save_config()
        except Exception as e:
            self.set_message('ERROR!!!\t' + str(e))
            if os.path.exists('temp'):
                os.rmdir('temp')

class DictionaryWindow(Window):
    """
    Окно составления справочника брендов
    """
    def __init__(self, proc_wind):
        """
        :param proc_wind: объект ProcessingWindow - окно вычислений приложения
        """
        super().__init__()
        
        # Окно вычислений
        self.proc_wind = proc_wind
        # Создание окна
        self.initUI()

    def initUI(self):
        """
        Создание окна
        """
        # Положение следующей строки по вертикали
        new_line_vert = self.margin_vert

        # Ввод название записываемого
        #   Подпись
        self.dict_name_label = QLabel(self)
        self.dict_name_label.setText('Название нового справочника:')
        self.dict_name_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.dict_name_line_edit = QLineEdit(self)
        self.dict_name_line_edit.move(self.margin_hor, new_line_vert)
        self.dict_name_line_edit.resize(self.input_line_wight, self.input_line_high)
        new_line_vert += self.input_line_high + self.space

        # Ввод пути к файлу со справочником
        #   Подпись
        self.dict_file_path_label = QLabel(self)
        self.dict_file_path_label.setText('Путь к excel файлу с информацией для справочника:')
        self.dict_file_path_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.dict_file_path_line_edit = QLineEdit(self)
        self.dict_file_path_line_edit.move(self.margin_hor, new_line_vert)
        self.dict_file_path_line_edit.resize(self.input_line_wight, self.input_line_high)
        #   Кнопка вызова диалогового окна выбора файла
        self.dict_file_path_btn = QPushButton('...', self)
        self.dict_file_path_btn.move(self.input_line_wight + self.margin_vert + self.space, new_line_vert)
        self.dict_file_path_btn.resize(self.file_path_btn_wight, self.file_path_btn_high)
        self.dict_file_path_btn.clicked.connect(self.dict_file_path_btn_click)
        new_line_vert += self.input_line_high + self.space

        # Ввод названия книги excel-файла со справочником, в котором содержится справочник
        #   Подпись
        self.dict_sheet_name_label = QLabel(self)
        self.dict_sheet_name_label.setText('Название книги содержащей информацию для справочника:')
        self.dict_sheet_name_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.dict_sheet_name_line_edit = QLineEdit(self)
        self.dict_sheet_name_line_edit.move(self.margin_hor, new_line_vert)
        self.dict_sheet_name_line_edit.resize(self.input_line_wight, self.input_line_high)
        new_line_vert += self.input_line_high + self.space

        # Ввод названия столбца справочника, содержащего название брендов
        #   Подпись
        self.brand_rightholders_title_col_name_label = QLabel(self)
        self.brand_rightholders_title_col_name_label.setText('Название столбца обозначений категорий:')
        self.brand_rightholders_title_col_name_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.brand_rightholders_title_col_name_text_edit = QTextEdit(self)
        self.brand_rightholders_title_col_name_text_edit.move(self.margin_hor, new_line_vert)
        self.brand_rightholders_title_col_name_text_edit.resize(self.input_line_wight, self.input_line_high)
        new_line_vert += self.input_line_high + self.space

        # Ввод названия столбца справочника, содержащего основные идентификаторы
        #   Подпись
        self.main_id_title_col_name_label = QLabel(self)
        self.main_id_title_col_name_label.setText('Название столбца основных идентификаторов:')
        self.main_id_title_col_name_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.main_id_title_col_name_text_edit = QTextEdit(self)
        self.main_id_title_col_name_text_edit.move(self.margin_hor, new_line_vert)
        self.main_id_title_col_name_text_edit.resize(self.input_line_wight, self.input_line_high)
        new_line_vert += self.input_line_high + self.space

        # Ввод названия столбца справочника, содержащего основные ограничивающие идентификаторы
        #   Подпись
        self.main_limit_id_title_col_name_label = QLabel(self)
        self.main_limit_id_title_col_name_label.setText('Название столбца основных ограничивающих идентификаторов:')
        self.main_limit_id_title_col_name_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.main_limit_id_title_col_name_text_edit = QTextEdit(self)
        self.main_limit_id_title_col_name_text_edit.move(self.margin_hor, new_line_vert)
        self.main_limit_id_title_col_name_text_edit.resize(self.input_line_wight, self.input_line_high)
        new_line_vert += self.input_line_high + self.space

        # Ввод названия столбца справочника, содержащего дополнительные ограничивающие идентификаторы
        #   Подпись
        self.add_limit_id_title_col_name_label = QLabel(self)
        self.add_limit_id_title_col_name_label.setText('Название столбца дополнительных ограничивающих идентификаторов:')
        self.add_limit_id_title_col_name_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.add_limit_id_title_col_name_text_edit = QTextEdit(self)
        self.add_limit_id_title_col_name_text_edit.move(self.margin_hor, new_line_vert)
        self.add_limit_id_title_col_name_text_edit.resize(self.input_line_wight, self.input_line_high)
        new_line_vert += self.input_line_high + self.space

        # Ввод названия столбца справочника, содержащего исключающие идентификаторы
        #   Подпись
        self.exclud_id_title_col_name_label = QLabel(self)
        self.exclud_id_title_col_name_label.setText('Название столбца исключающих идентификаторов:')
        self.exclud_id_title_col_name_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Строка ввода
        self.exclud_id_title_col_name_text_edit = QTextEdit(self)
        self.exclud_id_title_col_name_text_edit.move(self.margin_hor, new_line_vert)
        self.exclud_id_title_col_name_text_edit.resize(self.input_line_wight, self.input_line_high)
        new_line_vert += self.input_line_high + self.space

        # Кнопка запуска вычислений
        self.run_btn = QPushButton('ЗАПУСК', self)
        self.run_btn.resize(self.run_btn.sizeHint())
        self.run_btn.move(self.window_wight - self.run_btn.size().width() - self.margin_hor, self.window_high - self.run_btn.size().height() - self.margin_vert)
        self.run_btn.clicked.connect(self.run)

        # Отображение хода обработки
        #   Подпись
        self.proc_progress_label = QLabel(self)
        self.proc_progress_label.setText('Ход обработки:')
        self.proc_progress_label.move(self.margin_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Текстовое окно
        msg_window_high = self.window_high - 2 * self.margin_vert - self.run_btn.size().height() - new_line_vert
        self.proc_progress_text = QTextEdit(self)
        self.proc_progress_text.move(self.margin_hor, new_line_vert)
        self.proc_progress_text.resize(self.content_wight, msg_window_high)
        self.proc_progress_text.setReadOnly(True)
        new_line_vert += msg_window_high + self.space
        #   Заполнение редактирумых элементов окна значениями из конфигурационного файла, которыми эти элементы были заполнены при последнем успешном запуске вычислений
        self.load_config()
    
    def dict_file_path_btn_click(self):
        """
        Функция кнопки вызова диалогового окна выбора файла со справочником для строки ввода excel файла со справочником
        :return: в строку ввода обрабатываемого файла вводится путь к выбраному файлу
        """
        choosed_file_path = self.get_path_from_file_dialog('Справочник')
        if choosed_file_path != '':
            self.dict_file_path_line_edit.setText(choosed_file_path)
    
    def save_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых строк окна составления словаря, которые будут воспроизводиться при открытии окна в следующую сессию
        :return: файл json, содержащий значения редактируемых строк окна составления словаря
        """
        dict_win_config = {
                           'dict_name': self.dict_name_line_edit.text(),
                           'data_path': self.dict_file_path_line_edit.text(),
                           'dictinary_sheet_name': self.dict_sheet_name_line_edit.text(),
                           'brand_rightholders_title': self.brand_rightholders_title_col_name_text_edit.toPlainText(),
                           'main_identifires_title': self.main_id_title_col_name_text_edit.toPlainText(),
                           'main_limit_identifires_title': self.main_limit_id_title_col_name_text_edit.toPlainText(),
                           'add_limit_identifires_title': self.add_limit_id_title_col_name_text_edit.toPlainText(),
                           'excluding_identifires_title': self.exclud_id_title_col_name_text_edit.toPlainText()
                          }
        with open(os.path.join('config', 'dict_win_config.json'), 'w') as config_file:
            config_file.write(json.dumps(dict_win_config))

    def load_config(self):
        """
        Заполнение редактируемых элементов окна составления словаря значениями из сохраненного конфигурационного файла config\\dict_win_config.json, если он есть
        """
        try:
            with open(os.path.join('config', 'dict_win_config.json')) as config_file:
                dict_win_config = json.load(config_file)
            self.dict_name_line_edit.setText(dict_win_config['dict_name'])
            self.dict_file_path_line_edit.setText(dict_win_config['data_path'])
            self.dict_sheet_name_line_edit.setText(dict_win_config['dictinary_sheet_name'])
            self.brand_rightholders_title_col_name_text_edit.setText(dict_win_config['brand_rightholders_title'])
            self.main_id_title_col_name_text_edit.setText(dict_win_config['main_identifires_title'])
            self.main_limit_id_title_col_name_text_edit.setText(dict_win_config['main_limit_identifires_title'])
            self.add_limit_id_title_col_name_text_edit.setText(dict_win_config['add_limit_identifires_title'])
            self.exclud_id_title_col_name_text_edit.setText(dict_win_config['excluding_identifires_title'])
        except:
            print()

    def run(self):
        """
        Составление и сохранение справочника по параметрам, заданным в GUI, активируется кнопкой "ЗАПУСК"
        :return: составляет и сохраняет новый справочника в saves
        """
        try:
            # Начало отсчета таймера
            self.proc_begin_time = datetime.now()
            # Сбор данных из GUI
            #   Название составляемого справочника
            dict_name = self.dict_name_line_edit.text()
            #   Путь к excel файлу, с информацией для справочника
            data_path = self.dict_file_path_line_edit.text()
            #   Название книги содержащей информацию для справочника, если строка пустая, то берется первая книга в заданном файле
            dictinary_sheet_name = self.dict_sheet_name_line_edit.text()
            #   Название столбца обозначений категорий, если строка пустая, то берется первый столбец в заданной книге заданного файла
            brand_rightholders_title = self.brand_rightholders_title_col_name_text_edit.toPlainText()
            #   Название столбца основных идентификаторов, если строка пустая, то берется второй столбец в заданной книге заданного файла
            main_identifires_title = self.main_id_title_col_name_text_edit.toPlainText()
            #   Название столбца основных ограничивающих идентификаторов, если строка пустая, то берется третий столбец в заданной книге заданного файла
            main_limit_identifires_title = self.main_limit_id_title_col_name_text_edit.toPlainText()
            #   Название столбца дополнительных ограничивающих идентификаторов, если строка пустая, то берется четвертый столбец в заданной книге заданного файла
            add_limit_identifires_title = self.add_limit_id_title_col_name_text_edit.toPlainText()
            #   Название столбца исключающих идентификаторов, если строка пустая, то берется пятый столбец в заданной книге заданного файла
            excluding_identifires_title = self.exclud_id_title_col_name_text_edit.toPlainText()
            
            # Чтение данных из файла data_path
            with pd.ExcelFile(data_path) as reader:
                # Замена пустого значения страницы со справочником а название первой странице в файле
                if len(dictinary_sheet_name) == 0:
                    dictinary_sheet_name = reader.sheet_names[0]
                # Чтение книги excel файла с названием dictinary_sheet_name, содержащей обозначения брендов и их идентификаторы
                features_df = pd.read_excel(reader, sheet_name=dictinary_sheet_name)
                # Замена значений пустых строк на соответствующие значения, если необходимо
                if len(brand_rightholders_title) == 0:
                    brand_rightholders_title = features_df.columns[0]
                if len(main_identifires_title) == 0:
                    main_identifires_title = features_df.columns[1]
                if len(main_limit_identifires_title) == 0:
                    main_limit_identifires_title = features_df.columns[2]
                if len(add_limit_identifires_title) == 0:
                    add_limit_identifires_title = features_df.columns[3]
                if len(excluding_identifires_title) == 0:
                    excluding_identifires_title = features_df.columns[4]
                    
            # Сообщение о начале составления справочника
            self.set_message(self.countdown() + '\tСоставление справочника ' + '\"' + dict_name + '\"')
            self.set_message('\tпо файлу \"' + data_path + '\";')
            self.set_message('\tпо книге \"' + dictinary_sheet_name + '\";')
            self.set_message('\tстолбец категорий:\t\"' + brand_rightholders_title + '\";')
            self.set_message('\tстолбец глав. ид-ов:\t\"' + main_identifires_title + '\";')
            self.set_message('\tстолбец глав. огран. ид-ов:\t\"' + main_limit_identifires_title + '\";')
            self.set_message('\tстолбец доп. огран. ид-ов:\t\"' + add_limit_identifires_title + '\";')
            self.set_message('\tстолбец искл. ид-ов:\t\"' + excluding_identifires_title + '\"')
            # Создание объекта справочника
            brend_dict = BrendDictionary(features_df,
                                         brand_rightholders_title,
                                         main_identifires_title,
                                         main_limit_identifires_title,
                                         add_limit_identifires_title,
                                         excluding_identifires_title)
            # Сообщение о завершении составлния спраочника
            self.set_message(self.countdown() + '\tСправочник \"' + dict_name + '\" составлен')
            # Сообщение о начале сохранения справочника
            self.set_message(self.countdown() + '\tСохранение справочника \"' + dict_name + '\"')
            # Сохранение справочника
            brend_dict.save(dict_name)
            # Обновление списка справочников
            self.proc_wind.find_dictionaries()
            # Сообщение о завершении составлении справочника и его сохранение, вывод количества строк
            self.set_message(self.countdown() + '\tСправочник \"' + dict_name + '\" составлен и сохранен;')
            self.set_message('\tкол-во категорий в справочнике:\t' + str(len(brend_dict)))
            # Запись содержания строк окна в конфигурационный файл json, в следующую сессию эти строки записываются при открытии окна
            self.save_config()
        except Exception as e:
            self.set_message('ERROR!!!\t' + str(e))


class AppWindow(QWidget):

    def __init__(self):
        super().__init__()

        # Создание вкладок приложения
        proc_wind_tab = ProcessingWindow()
        dict_wind_tab = DictionaryWindow(proc_wind_tab)

        # Добавление владок в приложение
        self.tabs = QTabWidget()
        self.tabs.addTab(proc_wind_tab, "Вычисления")
        self.tabs.addTab(dict_wind_tab, "Справочник")

        # Создание макета приложения
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # Установка фикированного размера окна
        self.setFixedSize(self.sizeHint())

        # Название окна и логотип
        self.setWindowTitle('Category Recognizer')
        self.setWindowIcon(QIcon('NTech_logo.png'))
        

def run_app():
    # GUI
    app = QApplication(sys.argv)
    app_window = AppWindow()
    app_window.show()
    sys.exit(app.exec_())
