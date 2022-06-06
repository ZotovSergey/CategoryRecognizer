import pandas as pd
import os
import multiprocessing as mp

from DataProcessing.SKUPreprocessing import SKUReader

class BrendRecognizer:

    def __init__(self, brend_dictionary):
        self.brend_dictionary = brend_dictionary

    def process_rows(self, data_rows):
        pool = mp.Pool(self.cpu_count)
        brends_list = list(pool.map(self.brend_dictionary.identify_brend_cython, data_rows))
        pool.close()
        return brends_list
    
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

    def save_data_frame_to_excel(self, df_path_tuple):
        df = df_path_tuple[0]
        save_path = df_path_tuple[1]
        pd.DataFrame(df).to_excel(save_path, sheet_name=self.brend_sheet_name, index=False)

    def write_excel_files_batch(self, df_path_batch):
        pool = mp.Pool(self.cpu_count)
        with pool:
            pool.map(self.save_data_frame_to_excel, df_path_batch)
        pool.close()

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
