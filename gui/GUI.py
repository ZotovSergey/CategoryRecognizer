import sys
import os
import json
import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import QObject, QThread, pyqtSignal

import multiprocessing as mp

from DataProcessing.DataProcessing import CategoryRecognizer, SKUCleaner
from DataProcessing.SKUPreprocessing import CLEAR_PATTERNS_DICT, preprocess_sku_for_recognizing
from CategoryDirectory.CategoryDirectory import CategoryDirectory


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
        :param app_win: окно приложения
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
        self.pbar_label.setText('Прогресс раcпознавания:')
        tab_layout.addWidget(self.pbar_label)
        #   Progress bar
        self.pbar = ProgressBar(QProgressBar(self))
        tab_layout.addWidget(self.pbar.pbar)
        #       Обнуление progress bar
        self.pbar.reset(1)
        
        # Кнопки управления вычислениями
        #   Макет
        calc_command_btms_box = QHBoxLayout()
        tab_layout.addLayout(calc_command_btms_box)
        calc_command_btms_box.addStretch(1)
        #       Кнопка запуска вычислений
        self.run_btn = QPushButton('ЗАПУСК', self)
        self.run_btn.clicked.connect(self.start_thread)
        calc_command_btms_box.addWidget(self.run_btn)

        #   Заполнение редактирумых элементов окна значениями из конфигурационного файла, которыми эти элементы были заполнены при последнем успешном запуске вычислений
        self.load_config()
    
    def find_directories(self):
        """
        Находит названия доступных справочников в saves и добавляет их в комбобокс выбора справочника
        :return: добавляет названия доступных справочников в комбобокс выбора справочника
        """
        self.select_dir_combo.clear()
        try:
            dir_list = os.listdir('saves')
        except:
            dir_list = []
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
            pass
    
    def catch_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых элементов окна вычислений, которые будут воспроизводиться при открытии окна в следущую сессию
        :return: файл json, содержащий значения редактируемых элементов окна вычислений; если директория config отсутствует, создает ее
        """
        self.tab_config = {
                           'sel_dir': self.select_dir_combo.currentText(),
                           'input_data_path': self.input_file_path_line_edit.text(),
                           'sku_sheet_name': self.sku_sheet_name_line_edit.text(),
                           'sku_col_name': self.sku_col_name_text_edit.toPlainText(),
                           'output_data_path': self.output_file_path_line_edit.text(),
                           'use_threads_count': self.use_threads_count_line_edit.text(),
                           'max_batch_len': self.max_batch_len_line_edit.text(),
                           'dec_id': self.id_output_check.isChecked()
                          }

    def save_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых элементов окна вычислений, которые будут воспроизводиться при открытии окна в следущую сессию.
        Значения редактируемых элементов окна вычислений берутся из self.tab_config, которая предварительно записывается функцией self.catch_config()
        :return: файл json, содержащий значения редактируемых элементов окна вычислений; если директория config отсутствует, создает ее
        """
        if not os.path.exists('config'):
            os.makedirs('config')
        with open(os.path.join('config', 'proc_tab_config.json'), 'w') as config_file:
            config_file.write(json.dumps(self.tab_config))

    def start_thread(self):
        """
        Запускает функцию self.run() в отдельном потоке через функцию self.app_win.run_tab_func
        """
        self.app_win.run_tab_func(self)

    def run(self):
        """
        Запускает распознавание категорий по SKU из заданного обрабатываемого файла по выбранному справочнику. Обрабатывает SKU из обрабатываемого файла по батчам заданного размера
        используя заданный справочник категорий и записывает наименования категорий в csv файл по заданному пути.
        """
        try:
            try:
                # Сбор данных из GUI и определение параметров файла с данными для обработки, подготовка к началу рассчетов
                #   Загрузка выбранного справочника, по нему будет идти распознавание категорий
                sel_dir = load_directory(self.select_dir_combo.currentText())
                #   Сообщение о завершении загрузки справочника
                self.app_win.worker.set_message_to_gui_from_thread("".join(['Справочник \"', self.select_dir_combo.currentText(), '\" загружен для использования в дальнейшей обработки SKU']))
                #   Путь к файлу, со строками SKU для обработки
                input_data_path = self.input_file_path_line_edit.text()
                # Название листа, содержащей строки SKU для обработки, если строка пустая, то берется первый лист в заданном файле
                sku_sheet_name = self.sku_sheet_name_line_edit.text()
                #   Название столбца, содержащего строки SKU для обработки, если строка пустая, то берется первый столбец в заданном файле
                sku_col_name = self.sku_col_name_text_edit.toPlainText()
                #   Путь к файлу, в который будут выводиться результаты распознавания
                output_data_path = self.output_file_path_line_edit.text()
                #   Количество задействованых в вычислении потоков, если строка пустая, то берется максимальное доступное количество потоков
                use_threads_count = self.use_threads_count_line_edit.text()
                if len(use_threads_count) == 0 or int(use_threads_count) > self.cpu_max:
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
                # Флаг, означающий, что нужно выводить определяющие идентификаторы
                get_dec_id = self.id_output_check.isChecked()
                # Считывание содержания строк окна
                self.catch_config()
            except Exception as e:
                self.app_win.worker.set_message_to_gui_from_thread(error_message(str(e)))
                raise Exception("ERROR!!!")

            # Распознавание SKU из обрабатываемого файла в соответствии заданному справочнику и запись результатов обработки в обработанный файл
            CategoryRecognizer(input_data_path, sku_sheet_name, sku_col_name, output_data_path, sel_dir, max_batch_len, get_dec_id, use_threads_count,
            self.app_win.worker.set_message_to_gui, ThreadProgressBar(self.app_win.worker), self.app_win.is_running_flag)

            #   Сохранение считанных строк окна в конфигурационный файл json, в следующую сессию эти строки записываются при открытии окна
            try:
                self.save_config()
            except Exception as e:
                #self.app_win.worker.set_message_to_gui_from_thread(error_message(str(e)))
                self.app_win.info_win.set_message_to_gui(error_message(str(e)))
                raise Exception("ERROR!!!")
        except Exception as e:
            pass
        finally:
            # Сигнал о завершении процесса
            self.app_win.worker.finished.emit()
            

class DirectoryTab(AppGUI):
    """
    Вкладка составления справочника категорий. Наследует AppGUI.
    """
    def __init__(self, app_win):
        """
        :param app_win: окно приложения
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
        self.run_btn.clicked.connect(self.start_thread)
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
            pass
    
    def catch_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых строк окна составления справочника, которые будут воспроизводиться при открытии окна в следующую сессию
        :return: файл json, содержащий значения редактируемых строк окна составления справочника; если директория config отсутствует, создает ее
        """
        self.tab_config = {
                           'dir_name': self.dir_name_line_edit.text(),
                           'data_path': self.dir_file_path_line_edit.text(),
                           'directory_sheet_name': self.dir_sheet_name_line_edit.text(),
                           'category_rightholders_title': self.category_rightholders_title_col_name_text_edit.toPlainText(),
                           'main_identifiers_title': self.main_id_title_col_name_text_edit.toPlainText(),
                           'main_limit_identifiers_title': self.main_limit_id_title_col_name_text_edit.toPlainText(),
                           'add_limit_identifiers_title': self.add_limit_id_title_col_name_text_edit.toPlainText(),
                           'excluding_identifiers_title': self.exclud_id_title_col_name_text_edit.toPlainText()
                          }
    
    def save_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых элементов окна вычислений, которые будут воспроизводиться при открытии окна в следущую сессию.
        Значения редактируемых элементов окна вычислений берутся из self.tab_config, которая предварительно записывается функцией self.catch_config()
        :return: файл json, содержащий значения редактируемых элементов окна вычислений; если директория config отсутствует, создает ее
        """
        if not os.path.exists('config'):
            os.makedirs('config')
        with open(os.path.join('config', 'dir_tab_config.json'), 'w') as config_file:
            config_file.write(json.dumps(self.tab_config))

    def start_thread(self):
        """
        Запускает функцию self.run() в отдельном потоке через функцию self.app_win.run_tab_func
        """
        self.app_win.run_tab_func(self)
    
    def run(self):
        """
        Составление и сохранение справочника по параметрам, заданным в GUI, активируется кнопкой "ЗАПУСК"
        :return: составляет и сохраняет новый справочника в saves
        """
        try:
            # Сбор данных из GUI
            #   Название составляемого справочника
            dir_name = self.dir_name_line_edit.text()
            #   Путь к excel-файлу, с данными для справочника
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
            # Считывание содержания строк окна
            self.catch_config()

            # Создание объекта справочника
            category_dir = CategoryDirectory(
                                            dir_name,
                                            data_path,
                                            directory_sheet_name,
                                            category_rightholders_title,
                                            main_identifiers_title,
                                            main_limit_identifiers_title,
                                            add_limit_identifiers_title,
                                            excluding_identifiers_title,
                                            preprocess_sku_for_recognizing,
                                            self.app_win.worker.set_message_to_gui_from_thread
                                            )
            try:
                # Сообщение о начале сохранения справочника
                self.app_win.worker.set_message_to_gui_from_thread("".join(['Сохранение справочника \"', dir_name, '\"']))
                # Сохранение справочника
                save_directory(category_dir, dir_name)
                # Обновление списка справочников
                self.app_win.worker.update_dir_list_from_thread()
                # Сообщение о завершении составлении справочника и его сохранение, вывод количества строк
                self.app_win.worker.set_message_to_gui_from_thread("".join(['Справочник \"', dir_name, '\" составлен и сохранен']))
                # Сохранение считанных строк окна в конфигурационный файл json, в следующую сессию эти строки записываются при открытии окна
                self.save_config()
            except Exception as e:
                # Сообщение об ошибке
                self.app_win.worker.set_message_to_gui_from_thread(error_message(str(e)))
                raise Exception("ERROR!!!")
        except:
            pass
        finally:
            # Сигнал о завершении процесса
            self.app_win.worker.finished.emit()

def save_directory(dir, dir_name):
    """
    :param dir: справочик категорий - объект CategoryDirectory, который сохраняется в диреторию saves
    :param dir_name: название справочника категорий dir, под которым он будет сохраняться

    :return: сохраняет справочник dir в директорию saves с названием dir_name; если директория saves отсутствует, создает ее
    """
    if not os.path.exists('saves'):
        os.makedirs('saves')
    with open(os.path.join('saves', dir_name), 'wb') as file:
        pickle.dump(dir, file, protocol=pickle.HIGHEST_PROTOCOL)

def load_directory(dir_name):
    """
    Загружает справочник по заданному пути, если папка с сохраненными справочниками существует
    :param dir_name: путь до загружаемого справочника
    :return: справочник по заданному пути, объект CategoryDirectory
    """
    with open(os.path.join('saves', dir_name), 'rb') as file:
        return pickle.load(file)

class SKUCleanTab(AppGUI):
    """
    Вкладка очистки SKU. Наследует AppGUI.
    """
    def __init__(self, app_win):
        """
        :param app_win: окно приложения
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
        self.select_pattern_label = QLabel(self)
        self.select_pattern_label.setText('Выберите шаблон:')
        tab_layout.addWidget(self.select_pattern_label)
        #   Комбобокс
        self.select_pattern_combo = QComboBox(self)
        #       Заполнение комбобокса названиями сохраненных в saves справочников
        self.fill_pattern_combo()
        tab_layout.addWidget(self.select_pattern_combo)

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
        self.pbar_label.setText('Прогресс раcпознавания:')
        tab_layout.addWidget(self.pbar_label)
        #   Progress bar
        self.pbar = ProgressBar(QProgressBar(self))
        tab_layout.addWidget(self.pbar.pbar)
        #       Обнуление progress bar
        self.pbar.reset(1)
        
        # Кнопки управления вычислениями
        #   Макет
        calc_command_btms_box = QHBoxLayout()
        tab_layout.addLayout(calc_command_btms_box)
        calc_command_btms_box.addStretch(1)
        #       Кнопка запуска вычислений
        self.run_btn = QPushButton('ЗАПУСК', self)
        self.run_btn.clicked.connect(self.start_thread)
        calc_command_btms_box.addWidget(self.run_btn)

        #   Заполнение редактирумых элементов окна значениями из конфигурационного файла, которыми эти элементы были заполнены при последнем успешном запуске вычислений
        self.load_config()
    
    def fill_pattern_combo(self):
        """
        Заплняет комбобокс выбора шалона очистки
        :return: добавляет названия доступных шаблонов очистки в комбобокс выбора шаблона очистки
        """
        self.select_pattern_combo.clear()
        self.select_pattern_combo.addItems(CLEAR_PATTERNS_DICT.keys())
    
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
            with open(os.path.join('config', 'clean_tab_config.json')) as config_file:
                dir_tab_config = json.load(config_file)
            self.select_pattern_combo.setCurrentText(dir_tab_config['sel_pat'])
            self.input_file_path_line_edit.setText(dir_tab_config['input_data_path'])
            self.sku_col_name_text_edit.setText(dir_tab_config['sku_col_name'])
            self.output_file_path_line_edit.setText(dir_tab_config['output_data_path'])
            self.use_threads_count_line_edit.setText(dir_tab_config['use_threads_count'])
            self.max_batch_len_line_edit.setText(dir_tab_config['max_batch_len'])
            self.sku_sheet_name_line_edit.setText(dir_tab_config['sku_sheet_name'])
        except:
            pass
    
    def catch_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых элементов окна вычислений, которые будут воспроизводиться при открытии окна в следущую сессию
        :return: файл json, содержащий значения редактируемых элементов окна вычислений; если директория config отсутствует, создает ее
        """
        self.tab_config = {
                           'sel_pat': self.select_pattern_combo.currentText(),
                           'input_data_path': self.input_file_path_line_edit.text(),
                           'sku_sheet_name': self.sku_sheet_name_line_edit.text(),
                           'sku_col_name': self.sku_col_name_text_edit.toPlainText(),
                           'output_data_path': self.output_file_path_line_edit.text(),
                           'use_threads_count': self.use_threads_count_line_edit.text(),
                           'max_batch_len': self.max_batch_len_line_edit.text()
                          }

    def save_config(self):
        """
        Запись конфигурационного файла json, содержащего значения редактируемых элементов окна вычислений, которые будут воспроизводиться при открытии окна в следущую сессию.
        Значения редактируемых элементов окна вычислений берутся из self.tab_config, которая предварительно записывается функцией self.catch_config()
        :return: файл json, содержащий значения редактируемых элементов окна вычислений; если директория config отсутствует, создает ее
        """
        if not os.path.exists('config'):
            os.makedirs('config')
        with open(os.path.join('config', 'clean_tab_config.json'), 'w') as config_file:
            config_file.write(json.dumps(self.tab_config))


    def start_thread(self):
        """
        Запускает функцию self.run() в отдельном потоке через функцию self.app_win.run_tab_func
        """
        self.app_win.run_tab_func(self)
        #self.run()

    def run(self):
        """
        Запускает распознавание категорий по SKU из заданного обрабатываемого файла по выбранному справочнику. Обрабатывает SKU из обрабатываемого файла по батчам заданного размера
        используя заданный справочник категорий и записывает наименования категорий в csv файл по заданному пути.
        """
        try:
            try:
                # Сбор данных из GUI и определение параметров файла с данными для обработки, подготовка к началу рассчетов
                #   Название шаблона очистки SKU
                clean_pattern = self.select_pattern_combo.currentText()
                #   Путь к файлу, со строками SKU для обработки
                input_data_path = self.input_file_path_line_edit.text()
                # Название листа, содержащей строки SKU для обработки, если строка пустая, то берется первый лист в заданном файле
                sku_sheet_name = self.sku_sheet_name_line_edit.text()
                #   Название столбца, содержащего строки SKU для обработки, если строка пустая, то берется первый столбец в заданном файле
                sku_col_name = self.sku_col_name_text_edit.toPlainText()
                #   Путь к файлу, в который будут выводиться результаты распознавания
                output_data_path = self.output_file_path_line_edit.text()
                #   Количество задействованых в вычислении потоков, если строка пустая, то берется максимальное доступное количество потоков
                use_threads_count = self.use_threads_count_line_edit.text()
                if len(use_threads_count) == 0 or int(use_threads_count) > self.cpu_max:
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
                # Считывание содержания строк окна
                self.catch_config()
            except Exception as e:
                self.app_win.worker.set_message_to_gui_from_thread(error_message(str(e)))
                raise Exception("ERROR!!!")
            # Распознавание SKU из обрабатываемого файла в соответствии заданному справочнику и запись результатов обработки в обработанный файл
            SKUCleaner(input_data_path, sku_sheet_name, sku_col_name, output_data_path, max_batch_len, clean_pattern, use_threads_count,
            self.app_win.worker.set_message_to_gui_from_thread, ThreadProgressBar(self.app_win.worker), self.app_win.is_running_flag)
            #self.app_win.info_win.set_message_to_gui, self.pbar, self.app_win.is_running_flag)            

            # Сохранение считанных строк окна в конфигурационный файл json, в следующую сессию эти строки записываются при открытии окна
            try:
                self.save_config()
            except Exception as e:
                # Сообщение об ошибке
                self.app_win.worker.set_message_to_gui_from_thread(error_message(str(e)))
                raise Exception("ERROR!!!")
        except:
            pass
        finally:
            # Сигнал о завершении процесса
            self.app_win.worker.finished.emit()


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

    def set_message_to_gui(self, msg):
        """
        Записывает заданное сообщение msg в текстовое окно графического интерфейса self.proc_progress_text

        :param msg: строка сообщения (str)
        :param proc_progress_text: текстовое окно, в которое выводится сообщение (QTextEdit)

        :return: записывает msg в окно сообщений
        """
        self.proc_progress_text.append(msg)
        QApplication.processEvents()


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
            pass

        # Макет окна приложений
        app_layout = QVBoxLayout(self)

        # Вкладки
        #   Создание вкладок
        #       Вкладка распознования категорий
        self.proc_tab = ProcessingTab(self)
        #       Вкладка составления справочника категорий
        self.dir_tab = DirectoryTab(self)
        #       Вкладка очистки SKU
        self.clean_tab = SKUCleanTab(self)
        #   Окно вкладок вычислений
        tabs = QTabWidget()
        tabs.addTab(self.proc_tab, "Распознавание")
        tabs.addTab(self.dir_tab, "Справочник")
        tabs.addTab(self.clean_tab, "Очистка")

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

        # Кнопка остановки вычислений
        #   Макет
        stop_btm_box = QHBoxLayout()
        stop_btm_box.addStretch(1)
        #   Кнопка
        self.stop_btn = QPushButton('СТОП', self)
        self.stop_btn.setEnabled(False)
        stop_btm_box.addWidget(self.stop_btn)
        self.stop_btn.clicked.connect(self.stop)
        app_layout.addLayout(stop_btm_box)

        # Начальный размер окна приложения
        self.resize(self.window_wight, self.window_high)

    def enable_run_btns(self):
        """
        Делает кнопки "ЗАПУСК" каждой вкладки активыми, а кнопку "СТОП" основного окна неактивной
        """
        self.proc_tab.run_btn.setEnabled(True)
        self.dir_tab.run_btn.setEnabled(True)
        self.clean_tab.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def disable_run_btns(self):
        """
        Делает кнопку "СТОП" основного окна активной, а кнопки "ЗАПУСК" каждой вкладки неактивной
        """
        self.proc_tab.run_btn.setEnabled(False)
        self.dir_tab.run_btn.setEnabled(False)
        self.clean_tab.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def stop(self):
        """
        Остановка процесса обработки
        """
        # Cообщение о начале остановки обработки
        self.info_win.set_message_to_gui('Остановка процесса...')
        # Переключение флажка self.is_running на False, что и дает сигнал об остановки процесса
        self.is_running = False
    
    def is_running_flag(self):
        """
        Возвращает True, если обработка идет и False, если обработка была остановлена (флаг self.is_running)
        """
        return self.is_running
    
    def run_tab_func(self, tab):
        """
        Запуск функции run из вкладки tab с помощью отдельного потока
        """
        self.is_running = True
        # Создание потока
        self.thread = QThread()
        # Создание объекта Worker, исполняющего функцию tab.run
        self.worker = Worker(tab.run)
        # Привязывание потока
        self.worker.moveToThread(self.thread)
        # Подключение сигналов о начале работы к функции self.worker.run
        self.thread.started.connect(self.disable_run_btns)
        self.thread.started.connect(self.worker.run)
        # Подключение сигналов о выводе сообщений к информационному окну
        self.worker.message.connect(self.info_win.set_message_to_gui)
        # Если в выбранной вкладке есть progress bar, к нему подключаются сигналы об перезапуске и обновлении
        if hasattr(tab, "pbar"):
            self.worker.reset_progress.connect(tab.pbar.reset)
            self.worker.progress.connect(tab.pbar.set)
        # Сигнал об обновлении списка справочников во вкладке распознования категорий (дается после составления нового справочника для его добавления в список)
        self.worker.update_dir_list.connect(self.proc_tab.find_directories)
        # Сигнал о завершение потока
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.wait)
        self.worker.finished.connect(self.enable_run_btns)

        # Начало работы потока
        self.thread.start()


class ProgressBar:
    """
    Progress bar в виде графического интерфейса
    """

    def __init__(self, pbar):
        """
        :param pbar: виджет progress bar из PyQt (QProgressBar)
        """
        self.pbar = pbar
        # Значение отображаемой величины, соответствующее 100%
        self.max_value = 100
    
    def reset(self, max_value):
        """
        Перезапуск progress bar - присвоение максимального значения, соответствующего 100% и выставление нулевого значния.

        :param max_value: значение отображаемой величины, соответствующее 100%

        :return: progress bar присваивается максимальное значение, выставление нулевого значения
        """
        self.max_value = max_value
        self.set(0)
    
    def set(self, value):
        """
        Выставление значения progress bar

        :param value: выставляемое значение progress bar абсолютное)

        :return: на progress bar выставляется значение процента value от self.max_value
        """
        # Вычисление процентного значения, которое будет выставляться на progress bar
        pbar_value = int(value / self.max_value * 100)
        self.pbar.setValue(pbar_value)
        QApplication.processEvents()

def run_app():
    # GUI
    app = QApplication(sys.argv)
    app_window = AppWindow()
    app_window.show()
    sys.exit(app.exec_())


class Worker(QObject):
    """
    Класс запускающий функцию в отдельно процессе. Предусматривает сигналы о завершении работы процесса, вывод сообщений, управление progress bar через сигналы
    """
    # Сигнал о завершении процесса
    finished = pyqtSignal()
    # Сигнал о выводе сообщения
    message = pyqtSignal(str)
    # Сигнал об обновлении progress bar
    progress = pyqtSignal(int)
    # Сигнал о перезапуске progress bar
    reset_progress = pyqtSignal(int)
    # Сигнал о прерывании обработки
    stop_working = pyqtSignal()
    # Сигнал об обновлении списка справочников во вкладке распознования категорий
    update_dir_list = pyqtSignal()


    def __init__(self, func):
        super(Worker, self).__init__()
        # Исполняемая функция
        self.func = func
    
    def run(self):
        """
        Начало выполнения функции self.func
        """
        self.func()
    
    def set_message_to_gui_from_thread(self, msg):
        """
        Вывод сообщения msg из потока с помощью сигнала
        """
        self.message.emit(msg)
    
    def update_dir_list_from_thread(self):
        # Обновление списка справочников во вкладке распознования категорий (дается после составления нового справочника для его добавления в список)
        self.update_dir_list.emit()


class ThreadProgressBar:
    """
    Progress bar, управляемый через объект Worker с помощью сигналов progress и reset_progress в виде графического интерфейса
    """
    def __init__(self, worker):
        # Объкт Worker, из которого запускается progress bar
        self.worker = worker
    
    def reset(self, max_value):
        """
        Перезапуск progress bar - присвоение максимального значения, соответствующего 100% и выставление нулевого значния.

        :param max_value: значение отображаемой величины, соответствующее 100%

        :return: progress bar присваивается максимальное значение, выставление нулевого значения
        """
        self.worker.reset_progress.emit(max_value)
    
    def set(self, value):
        """
        Выставление значения progress bar

        :param value: выставляемое значение progress bar абсолютное)

        :return: на progress bar выставляется значение процента value
        """
        self.worker.progress.emit(value)
    
def error_message(msg):
    """
    Возвращает строку об ошибке (добавляет ERROR!!! к msg)
    """
    return " ".join(["ERROR!!!", msg])