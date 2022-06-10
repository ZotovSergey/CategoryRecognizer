from math import floor
import sys
import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator, QIcon

import multiprocessing as mp
from datetime import datetime

from DataProcessing.DataProcessing import BrendRecognizer
from BrendDictionary.BrendDictionary import BrendDictionary, find_all_dict, load_dictionary

def deltatime_to_str(time):
    hours, reminder = divmod(time.total_seconds(), 60)
    minutes, seconds = divmod(reminder, 60)
    hours_str = str(floor(hours))
    minutes_str = str(floor(minutes))
    if len(minutes_str) == 1:
        minutes_str = '0' + minutes_str
    seconds_str = str(floor(seconds))
    if len(seconds_str) == 1:
        seconds_str = '0' + seconds_str

    return ":".join([hours_str, minutes_str, seconds_str])


class Window(QWidget):
    """
    Окно приложения, содержит размеры и разметку
    """
    def __init__(self):
        super().__init__()
        # Ширина окна
        self.window_wight = 500
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

        self.setFixedSize(self.window_wight, self.window_high)
        self.setWindowTitle('Brend Recognizer')

    def get_path_from_file_dialog(self, dialog_name):
        """
        Выбор файла в диалоговом окне
        :param dialog_name: название диалогового окна
        
        :return: путь к выбранному файлу
        """
        return QFileDialog.getOpenFileName(self, dialog_name, os.path.join(os.path.splitdrive(os.path.abspath(__file__))[0], os.sep))[0]


class ProcessingWindow(Window):
    """
    Окно обработки данных
    """
    def __init__(self):
        super().__init__()
        
        # Максимальное число ядер
        self.cpu_max = mp.cpu_count()
        # Длина батча по умолчанию
        self.default_batch_len = 10000

        self.initUI()

    def initUI(self):
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
        #   Ввод количества ядер, использующихся при вычислениях
        #       Подпись
        self.use_kernels_count_label = QLabel(self)
        self.use_kernels_count_label.setText('Кол-во задействованных ядер:')
        self.use_kernels_count_label.move(self.margin_hor, new_line_vert)
        #   Ввод количества строк в батче
        #       Подпись
        self.use_kernels_count_label = QLabel(self)
        self.use_kernels_count_label.setText('Кол-во строк в батче:')
        self.use_kernels_count_label.move(self.second_col_hor, new_line_vert)
        new_line_vert += self.space_after_label_vert
        #   Ввод количества ядер, использующихся при вычислениях
        #       Строка ввода
        self.use_kernels_count_line_edit = QLineEdit(self)
        self.use_kernels_count_line_edit.move(self.margin_hor, new_line_vert)
        self.use_kernels_count_line_edit.resize(self.short_input_line_wight, self.input_line_high)
        self.use_kernels_count_line_edit.setValidator(QIntValidator())
        #           Ввод максимального кол-ва ядер, как значения по умолчанию
        self.max_kernel_btn_click()
        #       Кнопка ввода максимального кол-ва ядер для вычисления
        self.max_kernel_btn = QPushButton('MAX', self)
        self.max_kernel_btn.resize(self.max_kernel_btn.sizeHint())
        self.max_kernel_btn.move(self.margin_hor + self.short_input_line_wight + self.space, new_line_vert)
        self.max_kernel_btn.clicked.connect(self.max_kernel_btn_click)

        #   Ввод количества строк в батче
        #       Строка ввода
        self.batch_len_line_edit = QLineEdit(self)
        self.batch_len_line_edit.move(self.second_col_hor, new_line_vert)
        self.batch_len_line_edit.resize(self.short_input_line_wight, self.input_line_high)
        self.batch_len_line_edit.setValidator(QIntValidator())
        self.batch_len_line_edit.setText(str(self.default_batch_len))
        new_line_vert += self.input_line_high + self.space

        # # Таймер
        # timer = QTimer(self)
        # timer.timeout.connect(self.showCounter)

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
        choosed_file_path = self.get_path_from_file_dialog('Исходящий файл')
        if choosed_file_path != '':
            self.output_file_path_line_edit.setText(choosed_file_path)

    def max_kernel_btn_click(self):
        """
        Функция кнопки ввода максимального кол-ва ядер для вычисления
        :return: записывает в строку ввода используемого количества ядер максималього числа ядер
        """
        self.use_kernels_count_line_edit.setText(str(self.cpu_max))
    
    def find_dictionaries(self):
        """
        Находит названия доступных справочников и добавляет их в комбобокс выбора справочника
        :return: добавляет названия доступных справочников в комбобокс выбора справочника
        """
        self.select_dict_combo.clear()
        dict_list = find_all_dict()
        self.select_dict_combo.addItems(dict_list)
    
    def run(self):
        sel_dict = load_dictionary(self.select_dict_combo.currentText())
        input_data_path = self.input_file_path_line_edit.text()
        sku_col_name = self.sku_col_name_text_edit.toPlainText()
        output_data_path = self.output_file_path_line_edit.text()
        use_kernels_count = int(self.use_kernels_count_line_edit.text())
        batch_len = int(self.batch_len_line_edit.text())

        br = BrendRecognizer(sel_dict, cpu_count=use_kernels_count)
        if self.id_output_check.isChecked():
            br.process_csv_get_dec_id(input_data_path, output_data_path, rows_col_name=sku_col_name, batch_len=batch_len)
        else:
            br.process_csv(input_data_path, output_data_path, rows_col_name=sku_col_name, batch_len=batch_len)


class DictionaryWindow(Window):
    """
    Окно составления справочника брендов
    """
    def __init__(self, proc_wind):
        """
        :param proc_wind: объект ProcessingWindow - окно вычислений приложения
        """
        super().__init__()
        
        # Максимальное число ядер
        self.cpu_max = mp.cpu_count()
        # Длина батча по умолчанию
        self.default_batch_len = 100000
        # Окно вычислений
        self.proc_wind = proc_wind

        self.initUI()

    def initUI(self):
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

        # # Таймер
        # timer = QTimer(self)
        # timer.timeout.connect(self.showCounter)

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
    
    def dict_file_path_btn_click(self):
        """
        Функция кнопки вызова диалогового окна выбора файла со справочником для строки ввода excel файла со справочником
        :return: в строку ввода обрабатываемого файла вводится путь к выбраному файлу
        """
        choosed_file_path = self.get_path_from_file_dialog('Справочник')
        if choosed_file_path != '':
            self.dict_file_path_line_edit.setText(choosed_file_path)
    
    def set_message(self, msg):
        """ Записывает заданное сообщение msg в текстовое окно интерфейса self.dict_sheet_name_line_edit
        :param msg: строка сообщения
        :return: записывает msg в окно сообщений
        """
        self.proc_progress_text.append(msg)
        QApplication.processEvents()

    def run(self):
        """
        Составление и сохранение справочника по параметрам, заданным в GUI, активируется кнопкой "ЗАПУСК"
        :return: составляет и сохраняет новый справочника в saves
        """
        # Начало отсчета таймера
        proc_begin_time = datetime.now()
        # Сообщение о начале составления справочника
        msg = deltatime_to_str(datetime.now() - proc_begin_time) + '\tСоставление справочника ' + self.dict_name_line_edit.text()
        self.set_message(msg)
        # Сбор данных из GUI
        #   Путь к excel файлу, синформацией для справочника
        data_path = self.dict_file_path_line_edit.text()
        #   Название книги содержащей информацию для справочника
        dictinary_sheet_name = self.dict_sheet_name_line_edit.text()
        if dictinary_sheet_name == '':
            dictinary_sheet_name = None
        #   Название столбца обозначений категорий
        brand_rightholders_title = self.brand_rightholders_title_col_name_text_edit.toPlainText()
        if brand_rightholders_title == '':
            brand_rightholders_title = None
        #   Название столбца основных идентификаторов
        main_identifires_title = self.main_id_title_col_name_text_edit.toPlainText()
        if main_identifires_title == '':
            main_identifires_title = None
        #   Название столбца основных ограничивающих идентификаторов
        main_limit_identifires_title = self.main_limit_id_title_col_name_text_edit.toPlainText()
        if main_limit_identifires_title == '':
            main_limit_identifires_title = None
        #   Название столбца дополнительных ограничивающих идентификаторов
        add_limit_identifires_title = self.add_limit_id_title_col_name_text_edit.toPlainText()
        if add_limit_identifires_title == '':
            add_limit_identifires_title = None
        #   Название столбца исключающих идентификаторов
        excluding_identifires_title = self.exclud_id_title_col_name_text_edit.toPlainText()
        if excluding_identifires_title == '':
            excluding_identifires_title = None
        # Создание объекта справочника
        brend_dict = BrendDictionary(data_path, dictinary_sheet_name,
                                     brand_rightholders_title,
                                     main_identifires_title,
                                     main_limit_identifires_title,
                                     add_limit_identifires_title,
                                     excluding_identifires_title)
        # Сообщение о завершении составлния спраочника
        msg = deltatime_to_str(datetime.now() - proc_begin_time) + '\tСправочник составлен ' + self.dict_name_line_edit.text()
        self.set_message(msg)
        # Сообщение о начале сохранения справочника
        msg = deltatime_to_str(datetime.now() - proc_begin_time) + '\tСохранение справочника ' + self.dict_name_line_edit.text()
        self.set_message(msg)
        # Сохранение справочника
        brend_dict.save(self.dict_name_line_edit.text())
        # Обновление списка справочников
        self.proc_wind.find_dictionaries()
        # Сообщение о завершении составлении справочника и его сохранение, вывод количества строк
        msg = deltatime_to_str(datetime.now() - proc_begin_time) + '\tСправочник ' + self.dict_name_line_edit.text() + ' состаавлен и сохранен, кол-во строк: ' + str(len(brend_dict))
        self.set_message(msg)


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
