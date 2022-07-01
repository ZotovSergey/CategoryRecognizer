import pandas as pd
import numpy as np
import os
import multiprocessing as mp

from PyQt5.QtWidgets import QApplication

def get_batch(iterable, batch_len=1):
    """
    Генератор батчей по batch_len
    """
    iterable_len = len(iterable)
    for ndx in range(0, iterable_len, batch_len):
        yield iterable[ndx : min(ndx + batch_len, iterable_len)]


class CategoryRecognizer:
    """
    Распознаватель категорий по SKU из заданного файла по заданному справочнику. Обрабатывает SKU из заданного файла по батчам заданного размера используя заданный справочник категорий и записывает наименования
    категорий в csv файл по заданному пути. Поддерживает многопоточную обработку для ускорния вычислений.
    """
    def __init__(self, sku_reader, category_directory, max_batch_len=100000, get_dec_id=False, cpu_count=None):
        """
        :param sku_reader: ридер SKU из заданого файла (SKUReaderCSV, SKUReaderExcel)
        :param category_directory: справочник категорий, в соотвтствии с которым определяется категория по SKU (CategoryDirectory)
        :param max_batch_len: максимальное количество строк SKU, содержащихся в одном обрабатываемом батче
        :param get_dec_id: флаг, означающий, что нужно выводить определяющие идентификаторы (bool)
        :param cpu_count: количество потоков, использумых для обработки, если превышает максимально доступное оличество потоков, то применяетс максимально доступное количество (int)
        """
        self.sku_reader = sku_reader
        self.get_dec_id = get_dec_id
        self.category_directory = category_directory
        self.max_batch_len = max_batch_len

        # Количество задействованных потоков
        cpu_num = mp.cpu_count()
        if cpu_count is None or cpu_count > cpu_num:
            self.cpu_count = cpu_num
        else:
            self.cpu_count = cpu_count
        
        # Функция обработки строк зависит от ожидаемых данных
        if not self.get_dec_id:
            # Выводится только категория
            self.proc_func = self.process_rows
        else:
            # Выводится категория и идентификаторы, по которым алгоритм определил категорию
            self.proc_func = self.process_rows_get_dec_id
    
    def read_batch(self, batch_start):
        """
        Чтение батча (self.batch_len строк) из ридера self.sku_reader, начиная с batch_start, а также предобработка читаемых строк SKU

        :param batch_start: строка, с которой начинается читаемый батч, не считая заголовка

        :return: self.batch_len предобаботанных SKU строк из ридера self.sku_reader
        """
        return self.sku_reader.read(batch_start, self.batch_len)
    
    def process_rows(self, data_rows):
        """
        Обработка строк data_rows (предобработанных SKU) в формате pandas.DataFrame - распознавания категории по заданым строкам, соответствующих справочнику self.category_directory, с использованием
        self.cpu_count потоков одновременно

        :param data_rows: предобработанные строки SKU

        :return: список данных, содержащий: распознанные категории
        """ 
        # Создание пула потоков для self.cpu_count потоков
        pool = mp.Pool(self.cpu_count)
        # Распознование категорий в соответствии справочнику self.category_directory
        categorys_list = list(pool.map(self.category_directory.identify_category_cython, data_rows))
        # Закрытие пула потоков
        pool.close()
        return [categorys_list]
    
    def process_rows_get_dec_id(self, data_rows):
        """
        Обработка строк data_rows (предобработанных SKU) в формате pandas.DataFrame - распознавания категории по заданым строкам, соответствующих справочнику self.category_directory, с использованием
        self.cpu_count потоков одновременно, а также вывод определяющих идентификаторов - тех, по которым была найдена подходящая категория

        :param data_rows: предобработанные строки SKU

        :return: список данных, содержащий: распознанные категории, основные определяющие идентификаторы, основные ограничивающие определяющие идентификаторы, дополнительные
        ограничивающие определяющие идентификаторы
        """
        # Создание пула потоков для self.cpu_count потоков
        pool = mp.Pool(self.cpu_count)
        # Распознование категорий в соответствии справочнику self.category_directory
        categories_dec_id_list = list(pool.map(self.category_directory.identify_category_and_dec_id_cython, data_rows))
        # Закрытие пула потоков
        pool.close()
        # Распределение полученных данных по соответствующи переменным
        categories_dec_id_list = list(zip(*categories_dec_id_list))
        categories_list = categories_dec_id_list[0]
        main_dec_id_list = categories_dec_id_list[1]
        main_limit_dec_id_list = categories_dec_id_list[2]
        add_limit_dec_id_list = categories_dec_id_list[3]
        return categories_list, main_dec_id_list, main_limit_dec_id_list, add_limit_dec_id_list
    
    # def process_rows_and_history(self, data_rows):
    #     pool = mp.Pool(self.cpu_count)
    #     categories_history_zip = list(pool.map(self.category_directory.identify_category_and_history, data_rows))
    #     pool.close()
    #     categories_history_lists = list(zip(*categories_history_zip))
    #     categories_list = categories_history_lists[0]
    #     history_list = categories_history_lists[1]
    #     return categories_list, history_list
    
    def read_and_preprocess_pd_file_batches_pool(self, batches_starts_list):
        """
        Чтение self.cpu_count батчей из ридера self.sku_reader, начинающихся с batches_starts_list

        :param batches_starts_list: список номеров строк читаемого файла, с которых начинаются читаемые батчи (list)

        :return: self.cpu_count списков (батчей) прочитанных предобработанных и не предобработанных SKU, соответствено
        """
        # Создание пула потоков для len(batches_starts_list) потоков
        pool = mp.Pool(len(batches_starts_list))
        # Одновременное чтение и предобработка заданных батчей
        data_batches_list = list(pool.map(self.read_batch, batches_starts_list))
        # Закрытие пула потоков
        pool.close()
        # Распределение полученных данных по соответствующи переменным
        preprocessed_rows_batches_list = list(zip(*data_batches_list))[0]
        sku_rows_batches_list = list(zip(*data_batches_list))[1]
        return preprocessed_rows_batches_list, sku_rows_batches_list

    def write_csv_file(self, df_path_zip):
        """
        Запись в csv-файл по пути df_path_zip[1] фрейма df_path_zip[0]

        :param df_path_zip: кортеж фрейма данных, преднозначенных для записи и пути к csv-файлу, в который записываются данные

        :return: csv-файл по пути df_path_zip[1] с записанным фрймом данных df_path_zip[0]
        """
        df = df_path_zip[0]
        df.to_csv(df_path_zip[1], sep='\t', index=False, header=False)

    def write_csv_temp_files_batch(self, df_batch):
        """
        Одновременная запись фреймов из df_batch во временные csv-файлы

        :param df_batch: список фремов данных для записи во вреенные файлы (list)

        :return: csv-файлы в директории для временных файлов с фремами из df_batch
        """
        # Создание директории для временных файлов, если ее еще нет
        if not os.path.exists('temp'):
            os.makedirs('temp')
        # Пути к создаваемым файлам
        temp_files_path_list = list(map(os.path.join, len(df_batch) * ['temp'], list(map(str, np.arange(0, len(df_batch))))))
        # Создание пула потоков для len(df_batch) потоков
        pool = mp.Pool(len(df_batch))
        # Одновременная запись временных csv-файлов
        pool.map(self.write_csv_file, zip(df_batch, temp_files_path_list))
        # Закрытие пула потоков
        pool.close()

        return temp_files_path_list

    def process_data(self, output_data_path, gui_tab):
        """
        Распознование категорий по SKU из ридера self.sku_reader, в соотетствии справочнику self.category_directory, по батчам, с применением self.cpu_count потоков одновременно и
        запись полученных результатов в csv-файл output_data_path

        :param output_data_path: путь к csv-файлу, в который будут записываться результаты распознования категорий
        :param gui_tab: графический интерфейс, из которого запускаются вычисления

        :return: в csv-файл output_data_path записываются категории, определенными по SKU из ридера self.sku_reader, а также идентификаторы определяющую полученную категорию, если self.get_dec_id
        """
        # Обнуление progress bar
        gui_tab.pbar.setValue(0)

        # Количество обработанных батчей
        batches_done_num = 0

        # Определение количества строк в обрабатываемом файле
        rows_count = len(self.sku_reader)
        #   Сообщение о количестве строк в обрабатываемом файле
        gui_tab.app_win.info_win.set_massage_with_countdown('Обрабатываемый файл содержит ' + str(rows_count))
        
        # Определение оптиального количества батчей
        opt_batches_num = int(np.ceil(int(np.ceil(rows_count / self.max_batch_len)) / self.cpu_count) * self.cpu_count)
        
        # Длина оптимальных батчей
        self.batch_len = int(np.ceil(rows_count / opt_batches_num))

        #   Сообщение о создании обработанного файла
        gui_tab.app_win.info_win.set_massage_with_countdown('Обрабатываемый файл делится на ' + str(opt_batches_num) + ' батчей, приблизительно, по ' + str(self.batch_len) + ' строк')

        # Создание пустого обработанного файла, в который будут записываться результаты распознавания по батчам
        output_file_header = pd.DataFrame({'SKU': [], 'Возвращаемое значение': []})
        #   Добавление в создаваемый файл столбцов для записи определяющих идентификаторов, если это необходимо
        if self.get_dec_id:
            dec_id_header = pd.DataFrame({'Главный идентификатор': [], 'Главный ограничивающий идентификатор': [], 'Дополнительный ограничивающий идентификатор': []})
            output_file_header = pd.concat([output_file_header, dec_id_header], axis=1)
        output_file_header.to_csv(output_data_path, sep='\t', index=False)
        #   Сообщение о создании обработанного файла
        gui_tab.app_win.info_win.set_massage_with_countdown('Обработанный файл \"' + output_data_path + '\" создан')

        # Вычисление по батчам
        #   Создание генератора, берущего по self.cpu_count первых строк батчей, то есть столько, сколько будут загружаться и сохраняться одновременно
        batch_starts_gen = get_batch(np.arange(opt_batches_num) * self.batch_len, self.cpu_count)
        #   Обработка батчей по self.cpu_count штук
        for batches_starts_list in batch_starts_gen:
            # Загрузка и предобработка self.cpu_count батчей, вывод предобработанных строк SKU и исходных
            #   Сообщение о начале загрузки и предобработке батчей
            gui_tab.app_win.info_win.set_massage_with_countdown('Загружаются и предобрабатываются батчи №' + ', '.join(map(str, list(np.arange(batches_done_num + 1, batches_done_num + len(batches_starts_list) + 1)))))
            #   Процесс загрузки
            rows_batches_list, sku_batches_list = self.read_and_preprocess_pd_file_batches_pool(batches_starts_list)
            #   Сообщение о завершении загрузки и предобработке батчей
            gui_tab.app_win.info_win.set_massage_with_countdown('Батчи загружены и предобработаны')
            
            # Обработка каждого батча
            proc_data_batches_list = []
            for i, rows_batch in enumerate(rows_batches_list):
                # Сообщение о начале обработки батча
                gui_tab.app_win.info_win.set_massage_with_countdown('Обрабатывается батч №' + str(batches_done_num + 1 + i))
                # Процесс обработки
                proc_data_batches_list.append(self.proc_func(rows_batch))
                # Сообщение о окончании обработки батча
                gui_tab.app_win.info_win.set_massage_with_countdown('Батч обработан')
            
            # Добавление обработанных данных в обработанный файл
            #   Запись временных файлов обработанных данных, полученных из каждого батча
            #       Сообщение о начале записи обработанных данных
            gui_tab.app_win.info_win.set_massage_with_countdown('Сохранение полученных данных')
            #       Состаление фреймов с исходящими данными
            #           Столбцы с исходными SKU
            df_list = [{'SKU': sku_batches_list[i]} for i in range(len(sku_batches_list))]
            #           Перебор фремов, соответствующих батчам
            for i, df in enumerate(df_list):
                # Перебор столбцов исходящих данных сооттствующего батча
                for j, col in enumerate(proc_data_batches_list[i]):
                    # Добавление столба в соответствующий фрейм
                    df['ans' + str(j)] = col
            df_list = list(map(pd.DataFrame, df_list))
            #       Запись временных файлов с исходящими данными
            temp_files_path_list = self.write_csv_temp_files_batch(df_list)
            # #       Запись путей к временным файлам
            # temp_files_list = os.listdir('temp')
            # temp_files_path_list = list(map(os.path.join, ['temp'] * len(temp_files_list), temp_files_list))
            #   Запись исходящих данных из временых файлов в обработанный файл
            #       Открытие обработанного файла для добавления
            with open(output_data_path, "ab") as out_file:
                # Перебор временных файлов с исходящими данными
                for temp_path in temp_files_path_list:
                    # Открытие временного файла для чтения
                    with open(temp_path, "rb") as temp_file:
                        # Чтение данных из временного файла и их добавление в обработанный файл
                        out_file.write(temp_file.read())
                    # Удаление временного файла
                    os.remove(temp_path)
            #       Обновление количества обработанных батчей
            batches_done_num += len(batches_starts_list)
            #       Сообщение о завершении записи обработанных данных
            gui_tab.app_win.info_win.set_massage_with_countdown('(' + str(batches_done_num) + '/' + str(opt_batches_num) + ') ' + 'Полученные данные сохранены в обработанный файл')

            # Обновление project bar
            pbar_value = int(batches_done_num / opt_batches_num * 100)
            gui_tab.pbar.setValue(pbar_value)
            QApplication.processEvents()
        # Удаление дериктории temp
        os.rmdir('temp')
