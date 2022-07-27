import pandas as pd
import numpy as np
import os
import shutil
import multiprocessing as mp
import shutil 

from datetime import datetime

from DataProcessing.SKUPreprocessing import init_sku_reader, CLEAR_PATTERNS_DICT
from Utilities.Utilities import *

def get_batch(iterable, batch_len=1):
    """
    Генератор батчей по batch_len
    """
    iterable_len = len(iterable)
    for ndx in range(0, iterable_len, batch_len):
        yield iterable[ndx : min(ndx + batch_len, iterable_len)]

class ListWraper():
    """
    Класс содержащий некоторую функцию от одной переменно и может возвращать результат работы этой функции в списке. Используется, если одиночный результат использования некоторой
    функции должен быть в списке для правильности дльнейших вычислений
    """
    def __init__(self, func):
        """
        :param func: некоторая функция от одной переменной, возвращаемое значение которой должно быть в списке
        """
        self.func = func
    
    def func_return_in_list(self, input):
        """
        Возвращает результат функции self.func от переменной input в списке
        """
        return [self.func(input)]


class SKUProcessorInterface:
    def __init__(self, input_data_path, sku_sheet_name, sku_col_name, output_data_path, max_batch_len, use_threads_count, set_msg_func, pbar, is_running_flag=None):
        """
        :param input_data_path: путь к файлу, со строками SKU для обработки
        :param sku_sheet_name: название листа, содержащей строки SKU для обработки, если строка пустая, то берется первый лист в заданном файле
        :param sku_col_name: название столбца, содержащего строки SKU для обработки, если строка пустая, то берется первый столбец в заданном файле
        :param output_data_path: путь к файлу, в который будут выводиться результаты распознавания
        :param max_batch_len: максимальное количество строк SKU, содержащихся в одном обрабатываемом батче
        :param use_threads_count: количество потоков, использумых для обработки, если превышает максимально доступное оличество потоков, то применяетс максимально доступное количество (int)
        :param set_msg_func: функция вывода сообщения
        :param pbar: объект progress bar, содержащий функции reset, set
        :param is_running_flag: функция, возвращающая False, если вычисления были остановлены, по умолчанию None - при том вычисления не могут быть остановлены
        """
        self.output_data_path = output_data_path
        self.set_msg_func = set_msg_func
        self.pbar = pbar
        self.is_running_flag = is_running_flag

        # Маркер для остановки процесса
        self.process_is_running = True

        # Начало отсчета времени
        self.timer_start = datetime.now()
        try:
            # Сообщение о начале подготовки к обработке
            set_message_with_countdown('Подготовка к обработке', self.timer_start, self.set_msg_func)

            # Обнуление progress bar
            self.pbar.reset(1)

            # Количество обработанных батчей
            self.batches_done_num = 0
            
            #   Создание ридера SKU, соответствующего формату обрабатываемого файла
            sku_reader = init_sku_reader(input_data_path, sku_sheet_name, sku_col_name)
            
            # Количество задействованных потоков
            cpu_num = mp.cpu_count()
            if use_threads_count is None or use_threads_count > cpu_num:
                cpu_count = cpu_num
            else:
                cpu_count = use_threads_count
            
            # Определение количества строк в обрабатываемом файле
            self.rows_count = len(sku_reader)

            # 
            self.max_batch_len = max_batch_len

            # Определение оптимального количества батчей
            self.opt_batches_num = int(np.ceil(int(np.ceil(self.rows_count / max_batch_len)) / cpu_count) * cpu_count)

            # Назначение максимального значения progress bar
            self.pbar.reset(self.opt_batches_num)
            
            # Длина оптимальных батчей
            batch_len = int(np.ceil(self.rows_count / self.opt_batches_num))

            #
            self.sku_processor = SKUProcessor(sku_reader, batch_len, use_threads_count)

        except Exception as e:
            set_error_message(str(e), self.timer_start, set_msg_func)

    def process(self):
        try:
            # Вычисление по батчам
            #   Создание генератора, берущего по self.use_threads_count первых строк батчей, то есть столько, сколько будут загружаться и сохраняться одновременно
            batch_starts_gen = get_batch(np.arange(self.opt_batches_num) * self.sku_processor.batch_len, self.sku_processor.use_threads_count)
            #   Обработка батчей по self.cpu_count штук
            for batches_starts_list in batch_starts_gen:
                # Прервана ли работа
                if (self.is_running_flag is not None) and (not self.is_running_flag()):
                    set_message_with_countdown('Обработка остановлена', self.timer_start, self.set_msg_func)
                    break
                # Загрузка и предобработка self.cpu_count батчей, вывод предобработанных строк SKU и исходных
                #   Сообщение о начале загрузки и предобработке батчей
                set_message_with_countdown("".join(['Загружаются батчи №', ', '.join(map(str, list(np.arange(self.batches_done_num + 1, self.batches_done_num + len(batches_starts_list) + 1))))]), self.timer_start, self.set_msg_func)
                #   Процесс загрузки
                sku_batches_list = self.sku_processor.read_file_batches_pool(batches_starts_list)
                #   Сообщение о завершении загрузки и предобработке батчей
                set_message_with_countdown('Батчи загружены', self.timer_start, self.set_msg_func)
            
                # Обработка каждого батча
                proc_data_batches_list = []
                for i, sku_batch in enumerate(sku_batches_list):
                    # Сообщение о начале обработки батча
                    set_message_with_countdown("".join(['Обрабатывается батч №', str(self.batches_done_num + 1 + i)]), self.timer_start, self.set_msg_func)
                    # Процесс обработки
                    proc_data_batches_list.append(self.sku_processor.process_rows(sku_batch))
                    # Добавление исходных SKU в массив данных
                    proc_data_batches_list[i] = [[sku_batches_list[i][j]] + proc_data_batches_list[i][j] for j in range(len(sku_batches_list[i]))]
                    # Сообщение о окончании обработки батча
                    set_message_with_countdown('Батч обработан', self.timer_start, self.set_msg_func)

                # Добавление обработанных данных в обработанный файл
                #   Запись временных файлов обработанных данных, полученных из каждого батча
                #       Сообщение о начале записи обработанных данных
                set_message_with_countdown('Сохранение полученных данных', self.timer_start, self.set_msg_func)
                #       Запись временных файлов с исходящими данными
                temp_files_path_list = self.sku_processor.write_csv_temp_files_batches(proc_data_batches_list)
                
                #   Запись исходящих данных из временых файлов в обработанный файл
                #       Открытие обработанного файла для добавления
                with open(self.output_data_path, "ab") as out_file:
                    # Перебор временных файлов с исходящими данными
                    for temp_path in temp_files_path_list:
                        # Открытие временного файла для чтения
                        with open(temp_path, "rb") as temp_file:
                            # Чтение данных из временного файла и их добавление в обработанный файл
                            out_file.write(temp_file.read())
                        # Удаление временного файла
                        os.remove(temp_path)
                #       Обновление количества обработанных батчей
                self.batches_done_num += len(batches_starts_list)
                #       Сообщение о завершении записи обработанных данных
                set_message_with_countdown("".join(['(', str(self.batches_done_num), '/', str(self.opt_batches_num), ') ', 'Полученные данные сохранены в обработанный файл']), self.timer_start, self.set_msg_func)

                # Обновление project bar
                self.pbar.set(self.batches_done_num)

            #   Сообщение о завершении обработки
            if not self.is_running_flag:
                set_message_with_countdown('Распознвание категорий по SKU завершено, результаты сохранены в обработанный файл', self.timer_start, self.set_msg_func)
        except Exception as e:
            set_error_message(str(e), self.timer_start, self.set_msg_func)
        finally:
            # Удаление дериктории temp
            if os.path.exists('temp'):
                shutil.rmtree('temp')
    
    def stop(self):
        self.process_is_running = False
        set_message_with_countdown('Обработка останавливатся...', self.timer_start, self.set_msg_func)


class SKUProcessor:
    """
    Обработчик SKU. Содержит функции многопоточного чтения SKU из файла батчами с предобработкой, многопоточное применение на каждой строке батча SKU некоторой функции, многопоточная
    запись результатов обработки в единый файл.
    """
    def __init__(self, sku_reader, batch_len, use_threads_count):
        """
        :param input_data_path: путь к файлу, со строками SKU для обработки
        :param sku_sheet_name: название листа, содержащей строки SKU для обработки, если строка пустая, то берется первый лист в заданном файле
        :param sku_col_name: название столбца, содержащего строки SKU для обработки, если строка пустая, то берется первый столбец в заданном файле
        :param output_data_path: путь к файлу, в который будут выводиться результаты распознавания
        :param max_batch_len: максимальное количество строк SKU, содержащихся в одном обрабатываемом батче
        :param use_threads_count: количество потоков, использумых для обработки, если превышает максимально доступное оличество потоков, то применяетс максимально доступное количество (int)
        """
        self.sku_reader = sku_reader
        self.proc_func = None
        self.batch_len = batch_len
        self.use_threads_count = use_threads_count

    def read_batch(self, batch_start):
        """
        Чтение батча (self.batch_len строк) из ридера self.sku_reader, начиная с batch_start, а также предобработка читаемых строк SKU

        :param batch_start: строка, с которой начинается читаемый батч, не считая заголовка

        :return: self.batch_len предобаботанных SKU строк из ридера self.sku_reader
        """
        return self.sku_reader.read(batch_start, self.batch_len)
    
    def process_rows(self, data_rows):
        """
        Обработка строк data_rows (предобработанных SKU) в формате pandas.DataFrame функцией self.proc_func - распознавания категории по заданым строкам, соответствующих справочнику self.category_directory, с использованием self.cpu_count потоков одновременно

        :param data_rows: предобработанные строки SKU

        :return: список данных, возвращаемый функцией self.proc_func
        """ 
        # Создание пула потоков для self.use_threads_count потоков
        pool = mp.Pool(self.use_threads_count)
        # Распознование категорий в соответствии справочнику self.category_directory
        processed_rows = list(pool.map(self.proc_func, data_rows))
        # Закрытие пула потоков
        pool.close()
        return processed_rows
    
    def read_file_batches_pool(self, batches_starts_list):
        """
        Чтение len(batches_starts_list) батчей строк из ридера self.sku_reader, начинающихся с batches_starts_list и их предобработка

        :param batches_starts_list: список номеров строк читаемого файла, с которых начинаются читаемые батчи (list)

        :return: len(batches_starts_list) списков (батчей) прочитанных предобработанных и не предобработанных SKU, соответствено
        """
        # Создание пула потоков для len(batches_starts_list) потоков
        pool = mp.Pool(len(batches_starts_list))
        # Одновременное чтение и предобработка заданных батчей
        sku_rows_batches_list = list(pool.map(self.read_batch, batches_starts_list))
        # Закрытие пула потоков
        pool.close()

        return sku_rows_batches_list

    def write_rows_to_csv_file(self, rows_path_zip):
        """
        Запись в csv-файл по пути rows_path_zip[1] данных rows_path_zip[0]

        :param df_path_zip: кортеж фрейма данных, преднозначенных для записи и пути к csv-файлу, в который записываются данные

        :return: csv-файл по пути df_path_zip[1] с записанным фрймом данных df_path_zip[0]
        """
        df = pd.DataFrame(rows_path_zip[0])
        df.to_csv(rows_path_zip[1], sep='\t', index=False, header=False)

    def write_csv_temp_files_batches(self, rows_batches):
        """
        Одновременная запись фреймов из df_batch во временные csv-файлы

        :param rows_batch: список строк данных для записи во вреенные файлы (list)

        :return: csv-файлы в директории для временных файлов с фреймами из df_batch
        """
        # Создание директории для временных файлов, если ее еще нет
        if not os.path.exists('temp'):
            os.makedirs('temp')
        # Пути к создаваемым файлам
        temp_files_path_list = list(map(os.path.join, len(rows_batches) * ['temp'], list(map(str, np.arange(0, len(rows_batches))))))
        # Создание пула потоков для len(df_batch) потоков
        pool = mp.Pool(len(rows_batches))
        # Одновременная запись временных csv-файлов
        pool.map(self.write_rows_to_csv_file, zip(rows_batches, temp_files_path_list))
        # Закрытие пула потоков
        pool.close()

        return temp_files_path_list
        

"""
Распознование категорий по SKU из ридера self.sku_reader, в соответствии справочнику self.category_directory, по батчам, с применением self.cpu_count потоков одновременно и
запись полученных результатов в csv-файл output_data_path

:param output_data_path: путь к csv-файлу, в который будут записываться результаты распознования категорий
:param gui_tab: графический интерфейс, из которого запускаются вычисления

:return: в csv-файл output_data_path записываются категории, определенными по SKU из ридера self.sku_reader, а также идентификаторы определяющую полученную категорию, если get_dec_id
"""
class CategoryRecognizer(SKUProcessorInterface):
    """
    Распознаватель категорий по SKU из заданного файла по заданному справочнику. Обрабатывает SKU из заданного файла по батчам заданного размера используя заданный справочник категорий и записывает наименования
    категорий в csv файл по заданному пути. Поддерживает многопоточную обработку для ускорния вычислений. При инициализации в csv-файл output_data_path записываются исходные SKU и соответствующии им категории,
    определенные по идентификаторам из справочника category_directory, а также идентификаторы определяющую полученную категорию, если get_dec_id
    """
    def __init__(self, input_data_path, sku_sheet_name, sku_col_name, output_data_path, category_directory, max_batch_len, get_dec_id, use_threads_count, set_msg_func, pbar, is_running_flag=None):
        """
        :param input_data_path: путь к файлу, со строками SKU для обработки
        :param sku_sheet_name: название листа, содержащей строки SKU для обработки, если строка пустая, то берется первый лист в заданном файле
        :param sku_col_name: название столбца, содержащего строки SKU для обработки, если строка пустая, то берется первый столбец в заданном файле
        :param output_data_path: путь к файлу, в который будут выводиться результаты распознавания
        :param category_directory: справочник категорий, в соответствии с которым определяется категория по SKU (CategoryDirectory)
        :param max_batch_len: максимальное количество строк SKU, содержащихся в одном обрабатываемом батче
        :param get_dec_id: флаг, означающий, что нужно выводить определяющие идентификаторы (bool)
        :param use_threads_count: количество потоков, использумых для обработки, если превышает максимально доступное оличество потоков, то применяетс максимально доступное количество (int)
        :param set_msg_func: функция вывода сообщения
        :param pbar: объект progress bar, содержащий функции reset, set
        :param is_running_flag: функция, возвращающая False, если вычисления были остановлены, по умолчанию None - при том вычисления не могут быть остановлены
        """
        super(CategoryRecognizer, self).__init__(input_data_path, sku_sheet_name, sku_col_name, output_data_path, max_batch_len, use_threads_count, set_msg_func, pbar, is_running_flag)

        # Функция обработки строк зависит от ожидаемых данных
        if not get_dec_id:
            # Выводится только категория
            self.sku_processor.proc_func = category_directory.identify_category_cython
        else:
            # Выводится категория и идентификаторы, по которым алгоритм определил категорию
            self.sku_processor.proc_func = category_directory.identify_category_and_dec_id_cython

        try:
            # Сообщение о начале обработки
            set_msg_func('Распознование категорий по SKU')
            
            # Обработка
            #   Сообщение о начале обработки
            #   Добавочное сообщение о том, что выводятся определяющие идентификаторы
            if get_dec_id:
                id_output_add_msg = ' с выводом определяющих идентификаторов'
            else:
                id_output_add_msg = ''
            set_message_with_countdown("".join(['Распознование категорий по SKU', id_output_add_msg]), self.timer_start, set_msg_func)
            set_message_with_tab("".join(['из файла \"', input_data_path, '\";']), set_msg_func)
            if self.sku_processor.sku_reader.get_sku_excel_sheet() is not None:
                set_message_with_tab("".join(['лист SKU: \"', self.sku_processor.sku_reader.get_sku_excel_sheet(), '\";']), self.set_msg_func)
            set_message_with_tab("".join(['столбец SKU: \"', self.sku_processor.sku_reader.get_sku_column_name(), '\";']), self.set_msg_func)
            set_message_with_tab("".join(['кол-во задействованных потоков: ', str(self.sku_processor.use_threads_count), ';']), self.set_msg_func)
            set_message_with_tab("".join(['макс. кол-во строк в батче: ', str(self.max_batch_len), ';']), self.set_msg_func)
            set_message_with_tab(" ".join(['обрабатываемый файл содержит', str(self.rows_count), 'строк']), self.set_msg_func)
            set_message_with_tab(" ".join(['файл делится на', str(self.opt_batches_num), 'батчей, приблизительно, по', str(self.sku_processor.batch_len), 'строк']), self.set_msg_func)
            set_message_with_tab("".join(['результат обработки будет сохранен в файл: \"', output_data_path, '\"']), self.set_msg_func)
            
            # Назначение максимального значения progress bar
            self.pbar.reset(self.opt_batches_num)

            # Создание пустого обработанного файла, в который будут записываться результаты распознавания по батчам
            output_file_header = pd.DataFrame({'SKU': [], 'Возвращаемое значение': []})
            #   Добавление в создаваемый файл столбцов для записи определяющих идентификаторов, если это необходимо
            if get_dec_id:
                dec_id_header = pd.DataFrame({'Главный идентификатор': [], 'Главный ограничивающий идентификатор': [], 'Дополнительный ограничивающий идентификатор': []})
                output_file_header = pd.concat([output_file_header, dec_id_header], axis=1)
            output_file_header.to_csv(self.output_data_path, sep='\t', index=False)
            #   Сообщение о создании обработанного файла
            set_message_with_countdown("".join(['Обработанный файл \"', output_data_path, '\" создан']), self.timer_start, self.set_msg_func)

        except Exception as e:
            set_error_message(str(e), self.timer_start, self.set_msg_func)
        
        # Основные многопоточные вычисления
        self.process()


class SKUCleaner(SKUProcessorInterface):
    """
    Очистка SKU от лишней информации, характерной для любых случаев и приведенеи к более общему виду. Обрабатывает SKU из заданного файла по батчам заданного размера используя заданную функцию очистки clean_func.
    Поддерживает многопоточную обработку для ускорния вычислений. При инициализации в csv-файл output_data_path записываются исходные SKU и измененные по clean_func.
    """
    def __init__(self, input_data_path, sku_sheet_name, sku_col_name, output_data_path, max_batch_len, name_clean_func, use_threads_count, set_msg_func, pbar, is_running_flag=None):
        """
        :param input_data_path: путь к файлу, со строками SKU для обработки
        :param sku_sheet_name: название листа, содержащей строки SKU для обработки, если строка пустая, то берется первый лист в заданном файле
        :param sku_col_name: название столбца, содержащего строки SKU для обработки, если строка пустая, то берется первый столбец в заданном файле
        :param output_data_path: путь к файлу, в который будут выводиться результаты распознавания
        :param max_batch_len: максимальное количество строк SKU, содержащихся в одном обрабатываемом батче
        :param name_clean_func: название функции очистки (шаблона очистки) из библиотки CLEAR_PATTERNS_DICT
        :param use_threads_count: количество потоков, использумых для обработки, если превышает максимально доступное оличество потоков, то применяетс максимально доступное количество (int)
        :param set_msg_func: функция вывода сообщения (string)
        :param pbar: объект progress bar, содержащий функции reset, set
        :param is_running_flag: функция, возвращающая False, если вычисления были остановлены, по умолчанию None - при том вычисления не могут быть остановлены
        """
        super(SKUCleaner, self).__init__(input_data_path, sku_sheet_name, sku_col_name, output_data_path, max_batch_len, use_threads_count, set_msg_func, pbar, is_running_flag)

        # Функция очистки SKU
        self.sku_processor.proc_func = ListWraper(CLEAR_PATTERNS_DICT[name_clean_func]).func_return_in_list

        try:
            # Сообщение о начале обработки
            set_msg_func('Очистка SKU')
            
            # Обработка
            #   Сообщение о начале обработки
            set_message_with_countdown('Очистка SKU', self.timer_start, set_msg_func)
            set_message_with_tab("".join(['из шаблону \"', name_clean_func, '\";']), set_msg_func)
            set_message_with_tab("".join(['из файла \"', input_data_path, '\";']), set_msg_func)
            if self.sku_processor.sku_reader.get_sku_excel_sheet() is not None:
                set_message_with_tab("".join(['лист SKU: \"', self.sku_processor.sku_reader.get_sku_excel_sheet(), '\";']), self.set_msg_func)
            set_message_with_tab("".join(['столбец SKU: \"', self.sku_processor.sku_reader.get_sku_column_name(), '\";']), self.set_msg_func)
            set_message_with_tab("".join(['кол-во задействованных потоков: ', str(self.sku_processor.use_threads_count), ';']), self.set_msg_func)
            set_message_with_tab("".join(['макс. кол-во строк в батче: ', str(self.max_batch_len), ';']), self.set_msg_func)
            set_message_with_tab(" ".join(['обрабатываемый файл содержит', str(self.rows_count), 'строк']), self.set_msg_func)
            set_message_with_tab(" ".join(['файл делится на', str(self.opt_batches_num), 'батчей, приблизительно, по', str(self.sku_processor.batch_len), 'строк']), self.set_msg_func)
            set_message_with_tab("".join(['результат обработки будет сохранен в файл: \"', output_data_path, '\"']), self.set_msg_func)
            
            # Назначение максимального значения progress bar
            self.pbar.reset(self.opt_batches_num)

            # Создание пустого обработанного файла, в который будут записываться результаты распознавания по батчам
            output_file_header = pd.DataFrame({'SKU': [], 'Очищенные SKU': []})
            #   Добавление в создаваемый файл столбцов для записи определяющих идентификаторов, если это необходимо
            output_file_header.to_csv(self.output_data_path, sep='\t', index=False)
            #   Сообщение о создании обработанного файла
            set_message_with_countdown("".join(['Обработанный файл \"', output_data_path, '\" создан']), self.timer_start, self.set_msg_func)

        except Exception as e:
            set_error_message(str(e), self.timer_start, self.set_msg_func)
        
        # Основные многопоточные вычисления
        self.process()
