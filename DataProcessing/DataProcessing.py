from email import header
import pandas as pd
import numpy as np
import csv
import os
import multiprocessing as mp
import tempfile

from PyQt5.QtWidgets import QApplication

from DataProcessing.SKUPreprocessing import SKUReader, preprocess_sku_df

def get_batch(iterable, batch_len=1):
    iterable_len = len(iterable)
    for ndx in range(0, iterable_len, batch_len):
        yield iterable[ndx : min(ndx + batch_len, iterable_len)]


class BrendRecognizer:

    def __init__(self, brend_dictionary, cpu_count=None):
        self.brend_dictionary = brend_dictionary

        cpu_num = mp.cpu_count()
        if cpu_count is None or cpu_count > cpu_num:
            self.cpu_count = cpu_num
        else:
            self.cpu_count = cpu_count

    def process_rows(self, data_rows):
        pool = mp.Pool(self.cpu_count)
        brends_list = list(pool.map(self.brend_dictionary.identify_brend_cython, data_rows))
        pool.close()
        return brends_list
    
    def process_rows_get_dec_id(self, data_rows):
        pool = mp.Pool(self.cpu_count)
        brends_dec_id_list = list(pool.map(self.brend_dictionary.identify_brend_and_dec_id_cython, data_rows))
        pool.close()
        brends_dec_id_list = list(zip(*brends_dec_id_list))
        brends_list = brends_dec_id_list[0]
        main_dec_id_list = brends_dec_id_list[1]
        main_limit_dec_id_list = brends_dec_id_list[2]
        add_limit_dec_id_list = brends_dec_id_list[3]
        return brends_list, main_dec_id_list, main_limit_dec_id_list, add_limit_dec_id_list
    
    def process_rows_and_history(self, data_rows):
        pool = mp.Pool(self.cpu_count)
        brends_history_zip = list(pool.map(self.brend_dictionary.identify_brend_and_history, data_rows))
        pool.close()
        brends_history_lists = list(zip(*brends_history_zip))
        brends_list = brends_history_lists[0]
        history_list = brends_history_lists[1]
        return brends_list, history_list
    
    def read_excel_files_batch(self, excel_files_path_batch, sku_reader):
        pool = mp.Pool(self.cpu_count)
        data_batch = list(pool.map(sku_reader.get_sku_from_excel, excel_files_path_batch))
        pool.close()
        preprocessed_rows_batch = list(zip(*data_batch))[0]
        sku_rows_batch = list(zip(*data_batch))[1]
        return preprocessed_rows_batch, sku_rows_batch
    
    def read_and_preprocess_pd_file_batch(self, batch_start):
        try:
            sku_df = pd.read_csv(self.file_path, header=None, usecols=[self.rows_col_num], skiprows=batch_start + 1, nrows=self.batch_len, sep='\t').fillna('')
        except:
            sku_df = pd.read_excel(self.file_path, header=None, usecols=[self.rows_col_num], skiprows=batch_start + 1, nrows=self.batch_len).fillna('')
        return preprocess_sku_df(sku_df)
    
    def read_and_preprocess_pd_file_batches_pool(self, batches_starts_list):
        pool = mp.Pool(self.cpu_count)
        data_batches_list = list(pool.map(self.read_and_preprocess_pd_file_batch, batches_starts_list))
        pool.close()
        preprocessed_rows_batches_list = list(zip(*data_batches_list))[0]
        sku_rows_batches_list = list(zip(*data_batches_list))[1]
        return preprocessed_rows_batches_list, sku_rows_batches_list

    def save_data_frame_to_excel(self, df_path_tuple):
        df = df_path_tuple[0]
        save_path = df_path_tuple[1]
        pd.DataFrame(df).to_excel(save_path, sheet_name=self.brend_sheet_name, index=False)

    def write_excel_files_batch(self, df_path_batch):
        pool = mp.Pool(self.cpu_count)
        with pool:
            pool.map(self.save_data_frame_to_excel, df_path_batch)
        pool.close()
    
    def write_csv_file(self, df_path_zip):
        df = df_path_zip[0]
        df.to_csv(df_path_zip[1], sep='\t', index=False, header=False)

    def write_csv_temp_files_batch(self, df):
        temp_files_list = list(map(os.path.join, self.cpu_count * ['temp'], list(map(str, np.arange(0, self.cpu_count)))))
        
        pool = mp.Pool(self.cpu_count)
        with pool:
            pool.map(self.write_csv_file, zip(df, temp_files_list))
        pool.close()
    
    # def write_data_temp_file(self, df):
    #     temp = tempfile.TemporaryFile()
    #     df.to_csv(df_path_zip[1], sep='\t', index=False, header=False)

    # def write_data_temp_files_batch(self, df):
    #     temp_files_list = list(map(os.path.join, self.cpu_count * ['temp'], list(map(str, np.arange(0, self.cpu_count)))))
        
    #     pool = mp.Pool(self.cpu_count)
    #     with pool:
    #         pool.map(self.write_data_temp_file, zip(df, temp_files_list))
    #     pool.close()

    def process_excel_files_pool(self, excel_files_path_list, sku_sheet_name, sku_col_title, ret_data_folder_path, brend_sheet_name, suffix='Processed_', cpu_count=None):
        if isinstance(excel_files_path_list, str):
            excel_files_path_list = [excel_files_path_list]

        cpu_num = mp.cpu_count()
        if cpu_count is None or cpu_count > cpu_num:
            self.cpu_count = cpu_num
        else:
            self.cpu_count = cpu_count
        
        self.brend_sheet_name = brend_sheet_name

        sku_reader = SKUReader(sku_sheet_name, sku_col_title)

        excel_files_path_batches = [excel_files_path_list[i * self.cpu_count:(i + 1) * self.cpu_count]
                                    for i in range((len(excel_files_path_list) + self.cpu_count - 1) // self.cpu_count )]

        for excel_files_path_batch in excel_files_path_batches:
            preprocessed_rows_batch, sku_rows_batch = self.read_excel_files_batch(excel_files_path_batch, sku_reader)
            brends_lists_batch = []
            for preprocessed_rows in preprocessed_rows_batch:
                brends_lists_batch.append(self.process_rows(preprocessed_rows))
            df_path_batch = []
            for i in range(len(excel_files_path_batch)):
                save_path = os.path.join(ret_data_folder_path, suffix + os.path.basename(excel_files_path_batch[i]))
                df_path_batch.append((pd.DataFrame({'SKU': sku_rows_batch[i], 'Brend': brends_lists_batch[i]}), save_path))
            self.write_excel_files_batch(df_path_batch)
        
    def process_excel_files_pool_with_history(self, excel_files_path_list, sku_sheet_name, sku_col_title, ret_data_folder_path, brend_sheet_name, suffix='Processed_', cpu_count=None):
        if isinstance(excel_files_path_list, str):
            excel_files_path_list = [excel_files_path_list]

        cpu_num = mp.cpu_count()
        if cpu_count is None or cpu_count > cpu_num:
            self.cpu_count = cpu_num
        else:
            self.cpu_count = cpu_count
        
        self.brend_sheet_name = brend_sheet_name

        sku_reader = SKUReader(sku_sheet_name, sku_col_title)

        excel_files_path_batches = [excel_files_path_list[i * self.cpu_count:(i + 1) * self.cpu_count]
                                    for i in range((len(excel_files_path_list) + self.cpu_count - 1) // self.cpu_count )]

        for excel_files_path_batch in excel_files_path_batches:
            preprocessed_rows_batch, sku_rows_batch = self.read_excel_files_batch(excel_files_path_batch, sku_reader)
            brends_lists_batch = []
            history_lists_batch = []
            for preprocessed_rows in preprocessed_rows_batch:
                brends_list, history_list = self.process_rows_and_history(preprocessed_rows)
                brends_lists_batch.append(brends_list)
                history_lists_batch.append(history_list)
            df_path_batch = []
            for i in range(len(excel_files_path_batch)):
                save_path = os.path.join(ret_data_folder_path, suffix + os.path.basename(excel_files_path_batch[i]))
                df_path_batch.append((pd.DataFrame({'SKU': sku_rows_batch[i], 'Brend': brends_lists_batch[i], 'History': history_lists_batch[i]}), save_path))
            self.write_excel_files_batch(df_path_batch)
    
    def process_csv(self, csv_path, output_data_path, rows_col_name=None, batch_len=100000, get_dec_id=False, gui_window=None):
        # Количество обработанных батчей
        baches_done_num = 0
        # Путь к обрабатываемому файлу
        self.file_path = csv_path
        # Максимальный размер одного батча
        self.batch_len = batch_len

        # Определение количества строк в обрабатываемом файле
        rows_count = -1
        try:
            for line in csv.reader(open(self.file_path)):
                rows_count += 1
        except:
            rows_count = len(pd.read_excel(self.file_path)) - 1
        #   Сообщение о количестве строк вв обрабатываемом файле
        set_msg_in_gui('Обрабатываемый файл содержит ' + str(rows_count), gui_window)
        
        # Определение количества батчей
        batches_num = int(np.ceil(rows_count / batch_len))
        #   Сообщение о создании исходящего файла
        if gui_window is not None:
            gui_window.set_message(gui_window.countdown() + '\tОбрабатываемый файл делится на ' + str(batches_num) + ' батчей')

        # Определение порядкового номера столбца с SKU
        if rows_col_name is not None:
            try:
                self.rows_col_num = np.where(pd.read_csv(self.file_path, nrows=0, sep='\t').columns.values == rows_col_name)[0][0]
            except:
                self.rows_col_num = np.where(pd.read_excel(self.file_path, nrows=0).columns.values == rows_col_name)[0][0]
        else:
            self.rows_col_num = 0

        # Создание пустого исходящего файла, в который будут записываться результаты распознавания по батчам
        output_file_header = pd.DataFrame({'SKU': [], 'ans': []})
        #   Добавление в создаваемый файл столбцов для записи определяющих идентификаторов, если это необходимо
        if not get_dec_id:
            proc_func = self.process_rows
        else:
            proc_func = self.process_rows_get_dec_id
            dec_id_header = pd.DataFrame({'main identifier': [], 'main limiting identifier': [], 'additional limiting identifier': []})
            output_data_path = pd.concat([output_file_header, dec_id_header], axis=1)
        output_file_header.to_csv(output_data_path, sep='\t', index=False)
        #   Сообщение о создании исходящего файла
        set_msg_in_gui('Исходящий файл \"' + output_data_path + '\" создан', gui_window)

        # Вычисление по батчам
        #   Создание генератора, берущего по self.cpu_count первых строк батчей, то есть столько, сколько будут загружаться и сохраняться одновременно
        batch_starts_gen = get_batch(np.arange(batches_num) * batch_len, self.cpu_count)
        #   Обработка батчей по self.cpu_count штук
        for batches_starts_list in batch_starts_gen:
            # Загрузка и предобработка self.cpu_count батчей, вывод предобработанных строк SKU и исходных
            #   Сообщение о начале загрузки и предобработке батчей
            set_msg_in_gui('Загружаются и предобрабатываются батчи №' + ', '.join(map(str, list(np.arange(baches_done_num + 1, baches_done_num + self.cpu_count + 1)))), gui_window)
            #   Процесс загрузки
            rows_batches_list, sku_batches_list = self.read_and_preprocess_pd_file_batches_pool(batches_starts_list)
            #   Сообщение о завершении загрузки и предобработке батчей
            set_msg_in_gui('Батчи загружены и предобработаны', gui_window)
            
            # Обработка каждого батча
            proc_data_batches_list = []
            for i, rows_batch in enumerate(rows_batches_list):
                # Сообщение о начале обработки батча
                set_msg_in_gui('Обрабатывается батч №' + str(baches_done_num + 1 + i), gui_window)
                # Процесс обработки
                proc_data_batches_list.append([proc_func(rows_batch)])
                # Сообщение о окончании обработки батча
                set_msg_in_gui('Батч обработан', gui_window)
            
            # Добавление обработанных данных в исходящий файл
            #   Запись временных файлов обработанных данных, полученных из каждого батча
            #       Сообщение о начале записи обработанных данных
            set_msg_in_gui('Сохранение полученных данных', gui_window)
            #       Состаление фреймов с исходящими данными
            df_list = [{'SKU': sku_batches_list[i]} for i in range(len(sku_batches_list))]
            for i, df in enumerate(df_list):
                for j, col in enumerate(proc_data_batches_list[i]):
                    df['ans' + str(j)] = col
            df_list = map(pd.DataFrame, df_list)
            #       Запись временных файлов с исходящими данными
            self.write_csv_temp_files_batch(df_list)
            #       Запись путей к временным файлам
            temp_files_list = os.listdir('temp')
            temp_files_path_list = list(map(os.path.join, ['temp'] * len(temp_files_list), temp_files_list))
            #   Запись исходящих данных из временых файлов в исходящий файл
            #       Открытие исходящего файла для добавления
            with open(output_data_path, "ab") as out_file:
                # Перебор временных файлов с исходящими данными
                for temp_file_path in temp_files_path_list:
                    # Открытие временного файла для чтения
                    with open(temp_file_path, "rb") as temp_file:
                        # Чтение данных из временного файла и их добавление в исходящий файл
                        out_file.write(temp_file.read())
                    # Удаление временного файла
                    os.remove(temp_file_path)
            #       Обновление количества обработанных батчей
            baches_done_num += len(batches_starts_list)
            #       Сообщение о завершении записи обработанных данных
            set_msg_in_gui('(' + str(baches_done_num) + '/' + str(batches_num) + ') ' + 'Полученные данные сохранены в исходящий файл', gui_window)

            # Обновление project bar
            if gui_window is not None:
                pbar_value = int(baches_done_num / batches_num * 100)
                gui_window.pbar.setValue(pbar_value)
                QApplication.processEvents()

def set_msg_in_gui(msg, gui_win):
    if gui_win is not None:
        gui_win.set_message(gui_win.countdown() + '\t' + msg)
