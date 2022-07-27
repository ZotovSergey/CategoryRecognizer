import sys
import os
import shutil
import pandas as pd
import json

import chardet

from math import floor

from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QTabWidget, QFileDialog, QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QCheckBox, QProgressBar
from PyQt5.QtGui import QIntValidator, QIcon
#from PyQt5.QtCore import QRunnable, QThreadPool, pyqtSlot

import multiprocessing as mp
from datetime import datetime

from DataProcessing.DataProcessing import CategoryRecognizer
from DataProcessing.SKUPreprocessing import SKUReaderCSV, SKUReaderExcel
from CategoryDirectory.CategoryDirectory import CategoryDirectory, find_all_dir, load_directory


class AppGUI(QWidget):
    """
    Настройки графического интерфейса данного приложения, содержит некоторые размеры и функции, общие для графического интерфейса
    """
    def __init__(self):
        super().__init__()

        # Фиксированная высота текстовых окон для ввода имен олонок
        self.col_name_text_edit_high = 25
        # Ширина кнопки вызова окна выбора файла
        self.file_path_btn_wight = 30
        # Ширина короткой строки ввода
        self.short_input_line_wight = 100
    
    def get_path_from_open_file_dialog(self, dialog_name):
        """
        Выбор пути к существующему файлу в диалоговом окне
        
        :return: путь к выбранному существующему файлу
        """
        # Путь к директории, в которой открывается диалоговое окно
        initial_dir = os.path.join(os.path.splitdrive(os.path.abspath(__file__))[0], os.sep)
        # Диалоговое окно выбора существующего файла
        return QFileDialog.getOpenFileName(self, dialog_name, initial_dir)[0]

    def get_path_from_save_file_dialog(self, dialog_name):
        """
        Выбор пути к любому файлу в диалоговом окне
        
        :return: путь к любому выбранному файлу
        """
        # Путь к директории, в которой открывается диалоговое окно
        initial_dir = os.path.join(os.path.splitdrive(os.path.abspath(__file__))[0], os.sep)
        # Диалоговое окно выбора файла
        return QFileDialog.getSaveFileName(self, dialog_name, initial_dir)[0]


class ProcessingTab(AppGUI):
    """
    Вкладка распознавание категорий. Наследует AppGUI.
    """
    def __init__(self, app_win):
        """
        
        """
        super().__init__()
        
        # Максимальное число потоков
        self.cpu_max = mp.cpu_count()
        # Максимальная длина батча по умолчанию
        self.default_max_batch_len = 100000

        self.app_win = app_win
        # Создание окна
        self.initUI()
    
    def initUI(self):
        """
        Создание вкладки
        """
        # Макет вкладки
        tab_layout = QVBoxLayout(self)

        # Выбор справочника
        #   Подпись
        self.select_dir_label = QLabel(self)
        self.select_dir_label.setText('Выберите справочник:')
        tab_layout.addWidget(self.select_dir_label)
        #   Комбобокс
        self.select_dir_combo = QComboBox(self)
        #       Заполнение комбобокса названиями сохраненных в saves справочников
        self.find_directories()
        tab_layout.addWidget(self.select_dir_combo)

        # Ввод пути к обрабатываемому файлу
        #   Подпись
        self.input_file_path_label = QLabel(self)
        self.input_file_path_label.setText('Путь к обрабатываемому файлу:')
        tab_layout.addWidget(self.input_file_path_label)
        #   Макет строки ввода
        input_file_path_box = QHBoxLayout()
        tab_layout.addLayout(input_file_path_box)
        #       Строка ввода
        self.input_file_path_line_edit = QLineEdit(self)
        input_file_path_box.addWidget(self.input_file_path_line_edit)
        #       Кнопка вызова диалогового окна выбора файла
        self.input_file_path_btn = QPushButton('...', self)
        self.input_file_path_btn.clicked.connect(self.input_file_path_btn_click)
        self.input_file_path_btn.setFixedWidth(self.file_path_btn_wight)
        input_file_path_box.addWidget(self.input_file_path_btn)

        # Ввод названия листа SKU в обрабатываемом excel-файле
        #   Подпись
        self.sku_sheet_name_label = QLabel(self)
        self.sku_sheet_name_label.setText('Название листа SKU в обрабатываемом файле (если файл excel):')
        tab_layout.addWidget(self.sku_sheet_name_label)
        #   Строка ввода
        self.sku_sheet_name_line_edit = QLineEdit(self)
        tab_layout.addWidget(self.sku_sheet_name_line_edit)

        # Ввод названия столбца SKU в обрабатываемом файле
        #   Подпись
        self.sku_col_name_label = QLabel(self)
        self.sku_col_name_label.setText('Название столбца SKU в обрабатываемом файле:')
        tab_layout.addWidget(self.sku_col_name_label)
        #   Строка ввода
        self.sku_col_name_text_edit = QTextEdit(self)
        self.sku_col_name_text_edit.setFixedHeight(self.col_name_text_edit_high)
        tab_layout.addWidget(self.sku_col_name_text_edit)
        
        # Ввод пути к обработанному файлу
        #   Подпись
        self.output_file_path_label = QLabel(self)
        self.output_file_path_label.setText('Путь к обработанному файлу:')
        tab_layout.addWidget(self.output_file_path_label)
        #   Макет строки ввода
        output_file_path_box = QHBoxLayout()
        tab_layout.addLayout(output_file_path_box)
        #       Строка ввода
        self.output_file_path_line_edit = QLineEdit(self)
        output_file_path_box.addWidget(self.output_file_path_line_edit)
        #       Кнопка вызова диалогового окна выбора файла
        self.output_file_path_btn = QPushButton('...', self)
        self.output_file_path_btn.clicked.connect(self.output_file_path_btn_click)
        self.output_file_path_btn.setFixedWidth(self.file_path_btn_wight)
        output_file_path_box.addWidget(self.output_file_path_btn)

        # Чекбокс вывода идентификаторов
        self.id_output_check = QCheckBox("Выводить соответствующие идентифиаторы", self)
        tab_layout.addWidget(self.id_output_check)
        
        # Блок параметров вычислений
        #   Макет-сетка
        calc_param_block_grid = QGridLayout()
        calc_param_block_grid.setSpacing(2)
        tab_layout.addLayout(calc_param_block_grid)
        #   Ввод количества потоков, использующихся при вычислениях
        #       Подпись
        self.use_threads_count_label = QLabel(self)
        self.use_threads_count_label.setText('Кол-во задействованных потоков:')
        calc_param_block_grid.addWidget(self.use_threads_count_label, 1, 1)
        #       Макет строки ввода
        use_threads_count_box = QHBoxLayout()
        calc_param_block_grid.addLayout(use_threads_count_box, 1, 2)
        #           Строка ввода
        self.use_threads_count_line_edit = QLineEdit(self)
        self.use_threads_count_line_edit.setValidator(QIntValidator())
        self.use_threads_count_line_edit.setFixedWidth(self.short_input_line_wight)
        use_threads_count_box.addWidget(self.use_threads_count_line_edit)
        #           Кнопка ввода максимального кол-ва потоков для вычисления
        self.max_threads_btn = QPushButton('MAX', self)
        self.max_threads_btn.clicked.connect(self.max_threads_btn_click)
        use_threads_count_box.addWidget(self.max_threads_btn)
        use_threads_count_box.addStretch(1)
        #       Ввод максимального кол-ва ядер, как значения по умолчанию
        self.max_threads_btn_click()
        #   Ввод количества строк в батче
        #       Подпись
        self.use_batch_max_count_label = QLabel(self)
        self.use_batch_max_count_label.setText('Макс. кол-во строк в батче:')
        calc_param_block_grid.addWidget(self.use_batch_max_count_label, 2, 1)
        #       Строка ввода
        self.max_batch_len_line_edit = QLineEdit(self)
        self.max_batch_len_line_edit.setValidator(QIntValidator())
        self.max_batch_len_line_edit.setFixedWidth(self.short_input_line_wight)
        self.max_batch_len_line_edit.setText(str(self.default_max_batch_len))
        calc_param_block_grid.addWidget(self.max_batch_len_line_edit, 2, 2)

        # Отображение progress bar обработки
        #   Подпись
        self.pbar_label = QLabel(self)
        self.pbar_label.setText('Прогресс рапознавания:')
        tab_layout.addWidget(self.pbar_label)
        #   Progress bar
        self.pbar = QProgressBar(self)
        tab_layout.addWidget(self.pbar)
        #       Обнуление progress bar
        self.pbar.setValue(0)
        
        # Кнопки управления вычислениями
        #   Макет
        calc_command_btms_box = QHBoxLayout()
        tab_layout.addLayout(calc_command_btms_box)
        calc_command_btms_box.addStretch(1)
        #       Кнопка запуска вычислений
        self.run_btn = QPushButton('ЗАПУСК', self)
        self.run_btn.clicked.connect(self.run_calc)
        calc_command_btms_box.addWidget(self.run_btn)

        #   Заполнение редактирумых элементов окна значениями из конфигурационного файла, которыми эти элементы были заполнены при последнем успешном запуске вычислений
        self.load_config()
    
    def find_directories(self):
        """
        Находит названия доступных справочников в saves и добавляет их в комбобокс выбора справочника
        :return: добавляет названия доступных справочников в комбобокс выбора справочника
        """
        self.select_dir_combo.clear()
        dir_list = find_all_dir()
        self.select_dir_combo.addItems(dir_list)
    
    def input_file_path_btn_click(self):
        """
        Функция кнопки вызова диалогового окна выбора файла для строки ввода обрабатываемого файла
        :return: в строку ввода обрабатываемого файла вводится путь к выбраному файлу
        """
        choosed_file_path = self.get_path_from_open_file_dialog('Обрабатываемый файл')
        if choosed_file_path != '':
            self.input_file_path_line_edit.setText(choosed_file_path)
    
    def output_file_path_btn_click(self):
        """
        Функция кнопки вызова диалогового окна выбора файла для строки ввода обработанного файла
        :return: в строку ввода обработанного файла вводится путь к выбраному файлу
        """
        choosed_file_path = self.get_path_from_save_file_dialog('Обработанный файл')
        if choosed_file_path != '':
            self.output_file_path_line_edit.setText(choosed_file_path)
    
    def max_threads_btn_click(self):
        """
        Функция кнопки ввода максимального кол-ва потоков для вычисления
        :return: записывает в строку ввода используемого количества потоков максималього числа потоков
        """
        self.use_threads_count_line_edit.setText(str(self.cpu_max))
    
    def load_config(self):
        """
        Заполнение редактируемых элементов окна составления справочника значениями из сохраненного конфигурационного файла config\\proc_tab_config.json, если он есть
        """
        try:
            with open(os.path.join('config', 'proc_tab_config.json')) as config_file:
                dir_tab_config = json.load(config_file)
            self.select_dir_combo.setCurrentText(dir_tab_config['sel_dir'])
            self.input_file_path_line_edit.setText(dir_tab_config['input_data_path'])
            self.sku_col_name_text_edit.setText(dir_tab_config['sku_col_name'])
            self.output_file_path_line_edit.setText(dir_tab_config['output_data_path'])
            self.use_threads_count_line_edit.setText(dir_tab_config['use_threads_count'])
            self.max_batch_len_line_edit.setText(dir_tab_config['max_batch_len'])
            self.id_output_check.setChecked(dir_tab_config['dec_id'])
            self.sku_sheet_name_line_edit.setText(dir_tab_config['sku_sheet_name'])
        except:
            print()
    
    def save_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых элементов окна вычислений, которые будут воспроизводиться при открытии окна в следущую сессию
        :return: файл json, содержащий значения редактируемых элементов окна вычислений; если директория config отсутствует, создает ее
        """
        dir_tab_config = {
                          'sel_dir': self.select_dir_combo.currentText(),
                          'input_data_path': self.input_file_path_line_edit.text(),
                          'sku_sheet_name': self.sku_sheet_name_line_edit.text(),
                          'sku_col_name': self.sku_col_name_text_edit.toPlainText(),
                          'output_data_path': self.output_file_path_line_edit.text(),
                          'use_threads_count': self.use_threads_count_line_edit.text(),
                          'max_batch_len': self.max_batch_len_line_edit.text(),
                          'dec_id': self.id_output_check.isChecked()
                          }
        if not os.path.exists('config'):
            os.makedirs('config')
        with open(os.path.join('config', 'proc_tab_config.json'), 'w') as config_file:
            config_file.write(json.dumps(dir_tab_config))

    def run_calc(self):
        self.run_func()

        # worker = Worker(self.app_win, self.run_func)

        # self.app_win.threadpool.start(worker)

    def run_func(self):
        try:
            # Начало отсчета таймера
            self.app_win.info_win.reset_timer()
            # Сообщение о начале обработки
            self.app_win.info_win.set_massage('Распознование категорий по SKU')
            # Обнуление progress bar
            self.pbar.setValue(0)
            # Сбор данных из GUI и определение параметров файла с данными для обработки, подготовка к началу рассчетов
            #   Загрузка выбранного справочника, по нему будет идти распознавание категорий
            sel_dir = load_directory(self.select_dir_combo.currentText())
            #   Сообщение о завершении загрузки справочника
            self.app_win.info_win.set_massage_with_countdown('Справочник \"' + self.select_dir_combo.currentText() + '\" загружен')
            #   Путь к csv файлу, со строками SKU для обработки
            input_data_path = self.input_file_path_line_edit.text()
            #   Кодировка файла с данными
            encoding = None
            #   Лист excel-файла, содержащей строки SKU для обработки
            sku_sheet_name = None
            #   Определение расширения файла
            file_ext = input_data_path.split('.')[-1]
            #   Название столбца, содержащего строки SKU для обработки, если строка пустая, то берется первый столбец в заданном файле
            sku_col_name = self.sku_col_name_text_edit.toPlainText()
            #   Определение типа обрабатываемого файла и определение необходимых для полученного типа параметров
            if  file_ext in json.load(open(os.path.join('config', 'excel_ext.json')))['excel_ext']:
                # Формат обрабатываемого файла - excel
                # Название листа, содержащей строки SKU для обработки, если строка пустая, то берется первый лист в заданном файле
                sku_sheet_name = self.sku_sheet_name_line_edit.text()
                # Создание объекта-ридера SKU из excel-файла по пути input_data_path, из листа sku_sheet_name (или первого листа), из столбца sku_col_name (или первого столбца),
                # осуществляющего чтение и предобработку SKU
                sku_reader = SKUReaderExcel(input_data_path, sku_col_name, sku_sheet_name)
                # Заполнение пустого значения названия листа с SKU excel-файла
                if len(sku_sheet_name) == 0:
                    sku_sheet_name = sku_reader.sku_sheet_name
            else:
                # Формат обрабатываемого файла - csv, txt
                # Определение кодировки обрабатываемого файла
                #   Сообщение о начале определния кодировки
                self.app_win.info_win.set_massage_with_countdown('Определение кодировки обрабатываемого файла')
                encoding = chardet.detect(open(input_data_path, 'rb').read())['encoding']
                #   Сообщение о определенной кодировки
                self.app_win.info_win.set_massage_with_countdown('Кодировка обрабатываемого файла:\t\"' + encoding + '\"')
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
            self.app_win.info_win.set_massage_with_countdown('Распознование категорий по SKU' + id_output_add_msg)
            self.app_win.info_win.set_massage_with_tab('из файла \"' + input_data_path + '\";')
            self.app_win.info_win.set_massage_with_tab('столбец SKU: \"' + sku_col_name + '\";')
            self.app_win.info_win.set_massage_with_tab('кол-во задействованных потоков: ' + str(use_threads_count) + ';')
            self.app_win.info_win.set_massage_with_tab('макс. кол-во строк в батче: ' + str(max_batch_len) + ';')
            self.app_win.info_win.set_massage_with_tab('результат обработки будет сохранен в файл: \"' + output_data_path + '\"')
            #   Создание объекта, распознающего категории по SKU в соответствии справочнику sel_dir
            br = CategoryRecognizer(sku_reader, sel_dir, max_batch_len=max_batch_len, get_dec_id=self.id_output_check.isChecked(), cpu_count=use_threads_count)
            #   Распознавание SKU из заданного файла в соответствии заданному справочнику
            br.process_data(output_data_path, self)
            #   Сообщение о завершении обработки
            self.app_win.info_win.set_massage_with_countdown('Распознвание категорий по SKU завершено, результаты сохранены в обработанный файл')
            #   Запись содержания строк окна в конфигурационный файл json, в следующую сессию эти строки записываются при открытии окна
            self.save_config()
        except Exception as e:
            self.app_win.info_win.set_massage('ERROR!!!\t' + str(e))
            if os.path.exists('temp'):
                shutil.rmtree('temp')


class DirectoryTab(AppGUI):
    """
    Вкладка составления справочника категорий. Наследует AppGUI.
    """
    def __init__(self, app_win):
        """

        """
        super().__init__()

        self.app_win = app_win
        # Создание вкладки
        self.initUI()
    

    def initUI(self):
        """
        Создание вкладки
        """
        # Макет вкладки
        tab_layout = QVBoxLayout(self)

        # Ввод название записываемого
        #   Подпись
        self.dir_name_label = QLabel(self)
        self.dir_name_label.setText('Название нового справочника:')
        tab_layout.addWidget(self.dir_name_label)
        #   Строка ввода
        self.dir_name_line_edit = QLineEdit(self)
        tab_layout.addWidget(self.dir_name_line_edit)

        # Ввод пути к файлу со справочником
        #   Подпись
        self.dir_file_path_label = QLabel(self)
        self.dir_file_path_label.setText('Путь к excel-файлу с информацией для справочника:')
        tab_layout.addWidget(self.dir_file_path_label)
        #   Макет строки ввода
        dir_file_path_box = QHBoxLayout()
        tab_layout.addLayout(dir_file_path_box)
        #       Строка ввода
        self.dir_file_path_line_edit = QLineEdit(self)
        dir_file_path_box.addWidget(self.dir_file_path_line_edit)
        #       Кнопка вызова диалогового окна выбора файла
        self.dir_file_path_btn = QPushButton('...', self)
        self.dir_file_path_btn.setFixedWidth(self.file_path_btn_wight)
        self.dir_file_path_btn.clicked.connect(self.dir_file_path_btn_click)
        dir_file_path_box.addWidget(self.dir_file_path_btn)

        # Ввод названия листа excel-файла, в котором содержится справочник
        #   Подпись
        self.dir_sheet_name_label = QLabel(self)
        self.dir_sheet_name_label.setText('Название листа содержащей информацию для справочника:')
        tab_layout.addWidget(self.dir_sheet_name_label)
        #   Строка ввода
        self.dir_sheet_name_line_edit = QLineEdit(self)
        tab_layout.addWidget(self.dir_sheet_name_line_edit)

        # Ввод названия столбца справочника, содержащего название категорий
        #   Подпись
        self.category_rightholders_title_col_name_label = QLabel(self)
        self.category_rightholders_title_col_name_label.setText('Название столбца обозначений категорий:')
        tab_layout.addWidget(self.category_rightholders_title_col_name_label)
        #   Строка ввода
        self.category_rightholders_title_col_name_text_edit = QTextEdit(self)
        self.category_rightholders_title_col_name_text_edit.setFixedHeight(self.col_name_text_edit_high)
        tab_layout.addWidget(self.category_rightholders_title_col_name_text_edit)

        # Ввод названия столбца справочника, содержащего основные идентификаторы
        #   Подпись
        self.main_id_title_col_name_label = QLabel(self)
        self.main_id_title_col_name_label.setText('Название столбца основных идентификаторов:')
        tab_layout.addWidget(self.main_id_title_col_name_label)
        #   Строка ввода
        self.main_id_title_col_name_text_edit = QTextEdit(self)
        self.main_id_title_col_name_text_edit.setFixedHeight(self.col_name_text_edit_high)
        tab_layout.addWidget(self.main_id_title_col_name_text_edit)

        # Ввод названия столбца справочника, содержащего основные ограничивающие идентификаторы
        #   Подпись
        self.main_limit_id_title_col_name_label = QLabel(self)
        self.main_limit_id_title_col_name_label.setText('Название столбца основных ограничивающих идентификаторов:')
        tab_layout.addWidget(self.main_limit_id_title_col_name_label)
        #   Строка ввода
        self.main_limit_id_title_col_name_text_edit = QTextEdit(self)
        self.main_limit_id_title_col_name_text_edit.setFixedHeight(self.col_name_text_edit_high)
        tab_layout.addWidget(self.main_limit_id_title_col_name_text_edit)

        # Ввод названия столбца справочника, содержащего дополнительные ограничивающие идентификаторы
        #   Подпись
        self.add_limit_id_title_col_name_label = QLabel(self)
        self.add_limit_id_title_col_name_label.setText('Название столбца дополнительных ограничивающих идентификаторов:')
        tab_layout.addWidget(self.add_limit_id_title_col_name_label)
        #   Строка ввода
        self.add_limit_id_title_col_name_text_edit = QTextEdit(self)
        self.add_limit_id_title_col_name_text_edit.setFixedHeight(self.col_name_text_edit_high)
        tab_layout.addWidget(self.add_limit_id_title_col_name_text_edit)

        # Ввод названия столбца справочника, содержащего исключающие идентификаторы
        #   Подпись
        self.exclud_id_title_col_name_label = QLabel(self)
        self.exclud_id_title_col_name_label.setText('Название столбца исключающих идентификаторов:')
        tab_layout.addWidget(self.exclud_id_title_col_name_label)
        #   Строка ввода
        self.exclud_id_title_col_name_text_edit = QTextEdit(self)
        self.exclud_id_title_col_name_text_edit.setFixedHeight(self.col_name_text_edit_high)
        tab_layout.addWidget(self.exclud_id_title_col_name_text_edit)

        # Кнопки управления вычислениями
        #   Макет
        calc_command_btms_box = QHBoxLayout()
        tab_layout.addLayout(calc_command_btms_box)
        calc_command_btms_box.addStretch(1)
        #       Кнопка запуска вычислений
        self.run_btn = QPushButton('ЗАПУСК', self)
        self.run_btn.clicked.connect(self.run_calc)
        calc_command_btms_box.addWidget(self.run_btn)

        #   Заполнение редактирумых элементов окна значениями из конфигурационного файла, которыми эти элементы были заполнены при последнем успешном запуске вычислений
        self.load_config()

    def dir_file_path_btn_click(self):
        """
        Функция кнопки вызова диалогового окна выбора файла со справочником для строки ввода excel файла со справочником
        :return: в строку ввода обрабатываемого файла вводится путь к выбраному файлу
        """
        choosed_file_path = self.get_path_from_open_file_dialog('Справочник')
        if choosed_file_path != '':
            self.dir_file_path_line_edit.setText(choosed_file_path)

    def load_config(self):
        """
        Заполнение редактируемых элементов окна составления справочника значениями из сохраненного конфигурационного файла config\\dir_tab_config.json, если он есть
        """
        try:
            with open(os.path.join('config', 'dir_tab_config.json')) as config_file:
                dir_tab_config = json.load(config_file)
            self.dir_name_line_edit.setText(dir_tab_config['dir_name'])
            self.dir_file_path_line_edit.setText(dir_tab_config['data_path'])
            self.dir_sheet_name_line_edit.setText(dir_tab_config['directory_sheet_name'])
            self.category_rightholders_title_col_name_text_edit.setText(dir_tab_config['category_rightholders_title'])
            self.main_id_title_col_name_text_edit.setText(dir_tab_config['main_identifiers_title'])
            self.main_limit_id_title_col_name_text_edit.setText(dir_tab_config['main_limit_identifiers_title'])
            self.add_limit_id_title_col_name_text_edit.setText(dir_tab_config['add_limit_identifiers_title'])
            self.exclud_id_title_col_name_text_edit.setText(dir_tab_config['excluding_identifiers_title'])
        except:
            print()
    
    def save_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых строк окна составления справочника, которые будут воспроизводиться при открытии окна в следующую сессию
        :return: файл json, содержащий значения редактируемых строк окна составления справочника; если директория config отсутствует, создает ее
        """
        dir_tab_config = {
                          'dir_name': self.dir_name_line_edit.text(),
                          'data_path': self.dir_file_path_line_edit.text(),
                          'directory_sheet_name': self.dir_sheet_name_line_edit.text(),
                          'category_rightholders_title': self.category_rightholders_title_col_name_text_edit.toPlainText(),
                          'main_identifiers_title': self.main_id_title_col_name_text_edit.toPlainText(),
                          'main_limit_identifiers_title': self.main_limit_id_title_col_name_text_edit.toPlainText(),
                          'add_limit_identifiers_title': self.add_limit_id_title_col_name_text_edit.toPlainText(),
                          'excluding_identifiers_title': self.exclud_id_title_col_name_text_edit.toPlainText()
                         }
        if not os.path.exists('config'):
            os.makedirs('config')
        with open(os.path.join('config', 'dir_tab_config.json'), 'w') as config_file:
            config_file.write(json.dumps(dir_tab_config))

    def run_calc(self):
        self.run_func()

        # worker = Worker(self.app_win, self.run_func)

        # self.app_win.threadpool.start(worker)

    def run_func(self):
        """
        Составление и сохранение справочника по параметрам, заданным в GUI, активируется кнопкой "ЗАПУСК"
        :return: составляет и сохраняет новый справочника в saves
        """
        try:
            # Начало отсчета таймера
            self.app_win.info_win.reset_timer()
            # Сообщение о начале составления справочника
            self.app_win.info_win.set_massage('Составление справочника')
            # Сбор данных из GUI
            #   Название составляемого справочника
            dir_name = self.dir_name_line_edit.text()
            #   Путь к excel файлу, с информацией для справочника
            data_path = self.dir_file_path_line_edit.text()
            #   Название листа содержащей информацию для справочника, если строка пустая, то берется первый лист в заданном файле
            directory_sheet_name = self.dir_sheet_name_line_edit.text()
            #   Название столбца обозначений категорий, если строка пустая, то берется первый столбец в заданном листе заданного файла
            category_rightholders_title = self.category_rightholders_title_col_name_text_edit.toPlainText()
            #   Название столбца основных идентификаторов, если строка пустая, то берется второй столбец в заданном листе заданного файла
            main_identifiers_title = self.main_id_title_col_name_text_edit.toPlainText()
            #   Название столбца основных ограничивающих идентификаторов, если строка пустая, то берется третий столбец в заданном листе заданного файла
            main_limit_identifiers_title = self.main_limit_id_title_col_name_text_edit.toPlainText()
            #   Название столбца дополнительных ограничивающих идентификаторов, если строка пустая, то берется четвертый столбец в заданном листе заданного файла
            add_limit_identifiers_title = self.add_limit_id_title_col_name_text_edit.toPlainText()
            #   Название столбца исключающих идентификаторов, если строка пустая, то берется пятый столбец в заданном листе заданного файла
            excluding_identifiers_title = self.exclud_id_title_col_name_text_edit.toPlainText()

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
                    
            # Сообщение о начале составления справочника
            self.app_win.info_win.set_massage_with_countdown('Составление справочника ' + '\"' + dir_name + '\"')
            self.app_win.info_win.set_massage_with_tab('по файлу \"' + data_path + '\";')
            self.app_win.info_win.set_massage_with_tab('по листу \"' + directory_sheet_name + '\";')
            self.app_win.info_win.set_massage_with_tab('столбец категорий:\t\"' + category_rightholders_title + '\";')
            self.app_win.info_win.set_massage_with_tab('столбец глав. ид-ов:\t\"' + main_identifiers_title + '\";')
            self.app_win.info_win.set_massage_with_tab('столбец глав. огран. ид-ов:\t\"' + main_limit_identifiers_title + '\";')
            self.app_win.info_win.set_massage_with_tab('столбец доп. огран. ид-ов:\t\"' + add_limit_identifiers_title + '\";')
            self.app_win.info_win.set_massage_with_tab('столбец искл. ид-ов:\t\"' + excluding_identifiers_title + '\"')
            # Создание объекта справочника
            category_dir = CategoryDirectory(features_df,
                                         category_rightholders_title,
                                         main_identifiers_title,
                                         main_limit_identifiers_title,
                                         add_limit_identifiers_title,
                                         excluding_identifiers_title)
            # Сообщение о завершении составлния спраочника
            self.app_win.info_win.set_massage_with_countdown('Справочник \"' + dir_name + '\" составлен')
            # Сообщение о начале сохранения справочника
            self.app_win.info_win.set_massage_with_countdown('Сохранение справочника \"' + dir_name + '\"')
            # Сохранение справочника
            category_dir.save(dir_name)
            # Обновление списка справочников
            self.app_win.proc_tab.find_directories()
            # Сообщение о завершении составлении справочника и его сохранение, вывод количества строк
            self.app_win.info_win.set_massage_with_countdown('Справочник \"' + dir_name + '\" составлен и сохранен;')
            self.app_win.info_win.set_massage_with_tab('кол-во категорий в справочнике:\t' + str(len(category_dir)))
            # Запись содержания строк окна в конфигурационный файл json, в следующую сессию эти строки записываются при открытии окна
            self.save_config()
        except Exception as e:
            self.app_win.info_win.set_massage('ERROR!!!\t' + str(e))


class InfoWindow(AppGUI):
    """
    Информационное окно, в котором отображается информация о ходе вычислений. Наследует AppGUI.
    """
    def __init__(self):
        super().__init__()

        # Создание информационного окна
        self.initUI()
    
    def initUI(self):
        """
        Создание информационного окна
        """
        self.proc_progress_text = QTextEdit(self)
        self.proc_progress_text.setReadOnly(True)

    def reset_timer(self):
        """
        Начать отсчет времени. Текущее время записывается в поле self.calc_begin_time. Функция countdown возвращает отсчет времени от поля self.calc_begin_time.
        """
        self.calc_begin_time = datetime.now()
    
    def set_massage(self, msg):
        """
        Записывает заданное сообщение msg в текстовое окно интерфейса self.dir_sheet_name_line_edit
        :param msg: строка сообщения (str)
        :return: записывает msg в окно сообщений
        """
        self.proc_progress_text.append(msg)
        QApplication.processEvents()
    
    def set_massage_with_tab(self, msg):
        """
        Записывает заданное сообщение msg в текстовое окно интерфейса self.dir_sheet_name_line_edit и добавляет в начале табуляцию
        :param msg: строка сообщения (str)
        :return: записывает msg в окно сообщений
        """
        self.set_massage('\t' + msg)
    
    def set_massage_with_countdown(self, msg):
        """
        Записывает заданное сообщение msg в текстовое окно интерфейса self.dir_sheet_name_line_edit и добавляет в начале отсчет времени self.countdown()
        :param msg: строка сообщения (str)
        :return: записывает msg в окно сообщений
        """
        self.set_massage(self.countdown() + '\t' + msg)
    
    def countdown(self):
        """
        Вывод отсчета времени от заданного начала отчета времени self.calc_begin_time в формате строки 'h:mm:ss'
        :return: Отсчет времени от заданного начала отчета времени self.calc_begin_time в формате строки 'h:mm:ss'
        """
        # Вычисление времени от начала отсчета self.proc_begin_time
        time = datetime.now() - self.calc_begin_time
        # Вычисление целых часов, минут и секунд в time
        hours, reminder = divmod(time.total_seconds(), 3600)
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


class AppWindow(AppGUI):
    """
    Основное окно приложения. Наследует AppGUI
    """
    def __init__(self):
        super().__init__()

        # Начальная ширина окна приложения
        self.window_wight = 600
        # Начальная высота окна приложения
        self.window_high = 800

        #self.threadpool = QThreadPool()

        # Создание окна
        self.initUI()

    def initUI(self):
        """
        Создание окна приложения
        """

        # Название окна приложения
        self.setWindowTitle('Category Recognizer')

        # Установка логотипа приложения
        try:
            self.setWindowIcon(QIcon('NTech_logo.png'))
        except:
            print()

        # Макет окна приложений
        app_layout = QVBoxLayout(self)

        # Вкладки вычислений
        #   Создание вкладок вычислений
        self.proc_tab = ProcessingTab(self)
        self.dir_tab = DirectoryTab(self)
        #   Окно вкладок вычислений
        tabs = QTabWidget()
        tabs.addTab(self.proc_tab, "Распознавание")
        tabs.addTab(self.dir_tab, "Справочник")
        #   Макет окна
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(tabs)
        #   Бокс
        group_box_tabs = QGroupBox()
        group_box_tabs.setTitle('Вычисления')
        group_box_tabs.setLayout(tab_layout)

        app_layout.addWidget(group_box_tabs)

        # Информационное окно
        self.info_win = InfoWindow()
        #   Макет
        info_win_layout = QVBoxLayout()
        info_win_layout.addWidget(self.info_win.proc_progress_text)
        #   Бокс
        info_win_box = QGroupBox()
        info_win_box.setTitle('Ход вычислений:')
        info_win_box.setLayout(info_win_layout)

        app_layout.addWidget(info_win_box)

        # # Кнопка остановки вычислений
        # #   Макет
        # stop_btm_box = QHBoxLayout()
        # stop_btm_box.addStretch(1)
        # #   Кнопка
        # self.stop_btn = QPushButton('СТОП', self)
        # self.stop_btn.clicked.connect(self.stop)
        # self.stop_btn.setEnabled(False)
        # stop_btm_box.addWidget(self.stop_btn)

        # app_layout.addLayout(stop_btm_box)

        # Начальный размер окна приложения
        self.resize(self.window_wight, self.window_high)
    
    # def stop(self):
    #     print()

    def enable_run_btns(self):
        self.proc_tab.run_btn.setEnabled(True)
        self.dir_tab.run_btn.setEnabled(True)
        # self.stop_btn.setEnabled(False)

    def disable_run_btns(self):
        self.proc_tab.run_btn.setEnabled(False)
        self.dir_tab.run_btn.setEnabled(False)
        # self.stop_btn.setEnabled(True)

def run_app():
    # GUI
    app = QApplication(sys.argv)
    app_window = AppWindow()
    app_window.show()
    sys.exit(app.exec_())


# class Worker(QRunnable):
#     """
    
#     """
#     def __init__(self, app_win, func, *args, **kwargs):
#         super(Worker, self).__init__()
#         self.func = func
#         self.args = args
#         self.kwargs = kwargs

#         self.app_win = app_win
    
#     @pyqtSlot()
#     def run(self):
        
#         self.app_win.enable_run_btns()

#         self.func(*self.args, **self.kwargs)

#         self.app_win.disable_run_btns()
    
    
