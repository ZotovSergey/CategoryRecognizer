from datetime import datetime

from DataProcessing.DataProcessing import BrendRecognizer
from BrendDictionary.BrendDictionary import BrendDictionary

from DataProcessing.SKUPreprocessing import SKUReader

if __name__== "__main__":
    data_path = 'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки_+РЕЗУЛЬТАТ_РАЗМЕТКИ.xlsx'
    dictinary_sheet_name = 'Справочник идентиф-ов категорий'
    sku_sheet_name = 'СПИСОК SKU ДЛЯ РАЗМЕТКИ'
    ret_data_folder_path = 'D:\Data\МегаПоиск\Return'
    sku_col_title = 'SKU ДЛЯ РАЗМЕТКИ'
    brend_sheet_name = 'SKU'

    # excel_files_path_batch = [
    #                           'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки (часть).xlsx',
    #                           'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки (часть2).xlsx',
    #                           'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки (часть3).xlsx',
    #                           'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки (часть4).xlsx',
    #                           'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки (часть5).xlsx',
    #                           'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки (часть6).xlsx',
    #                           'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки (часть7).xlsx',
    #                           'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки (часть8).xlsx',
    #                           'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки (часть9).xlsx',
    #                          ]

    excel_file_path = 'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки.xlsx'


    s = datetime.now()
    brend_dict = BrendDictionary(data_path, dictinary_sheet_name)

    #brend_dict.identify_brend(' 133*: Кн.Нов.кн.с волшеб.лаб.и ч '.upper())

    A = BrendRecognizer(brend_dict)
    A.process_excel_files_pool_with_history(excel_file_path, sku_sheet_name, sku_col_title, ret_data_folder_path, brend_sheet_name, suffix='HISTORY_')
    #A.process_data_from_excel(data_path, sku_sheet_name, 'SKU ДЛЯ РАЗМЕТКИ', ret_data_folder_path, suffix='Processed_', brend_sheet_name='Brends')
    print(datetime.now() - s)
    # data_path = 'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки.xlsx'
    # dictinary_sheet_name = 'Справочник идентиф-ов категорий'
    # sku_sheet_name = 'СПИСОК SKU ДЛЯ РАЗМЕТКИ'

    # s = datetime.now()
    # brend_dict = BrendDictionary(data_path, dictinary_sheet_name)
    # print(datetime.now() - s)
    # sku_df, a = get_sku_from_excel(data_path, sku_sheet_name, sku_col_title='SKU ДЛЯ РАЗМЕТКИ')
    
    # print(datetime.now() - s)
    # pool = mp.Pool(mp.cpu_count())
    # A = list(pool.map(brend_dict.identify_brend_cython, sku_df))
    # pool.close()
    # print(datetime.now() - s)
    #print(A)

# if __name__== "__main__":
#     #data_path = 'D:\Data\МегаПоиск\Справочник_идентификаторов_и_SKU_для_разметки.xlsx'
#     data_path = 'D:\Data\МегаПоиск\Выборка_для_ПОИСК_ИЗ_МАССИВА.xlsx'
#     #dictinary_sheet_name = 'Справочник идентиф-ов категорий'
#     dictinary_sheet_name = 'Лист1'
#     #sku_sheet_name = 'СПИСОК SKU ДЛЯ РАЗМЕТКИ'
#     sku_sheet_name = 'Лист1'

#     s = datetime.now()
#     #brend_dict = BrendDictionary(data_path, dictinary_sheet_name)
#     brend_dict = BrendDictionary(data_path, dictinary_sheet_name,
#                                  brand_rightholders_title='Brand-Rightholder',
#                                  main_identifires_title='ОСНОВНЫЕ ИДЕНТИФИКАТОРЫ (КАТЕГОРИИ)\n(СОДЕРЖИТ)',
#                                  main_limit_identifires_title='ОСНОВН.ОГРАНИЧИВАЮЩИЕ ИДЕНТИФИКАТОРЫ\n(И СОДЕРЖИТ)',
#                                  add_limit_identifires_title='ДОП.ОГРАНИЧИВАЮЩИЕ ИДЕНТИФИКАТОРЫ\n(И СОДЕРЖИТ)',
#                                  excluding_identifires_title='ИСКЛЮЧАЮЩИЕ ИДЕНТИФИКАТОРЫ\n(НЕ СОДЕРЖИТ)')
#     print(datetime.now() - s)
#     #sku_df = get_sku(data_path, sku_sheet_name, sku_col_title='SKU ДЛЯ РАЗМЕТКИ')
#     sku_df = get_sku(data_path, sku_sheet_name, sku_col_title='SKU')
    
#     print(datetime.now() - s)
#     pool = mp.Pool(mp.cpu_count())
#     A = list(pool.map(brend_dict.identify_brend_cython, sku_df))
#     pool.close
#     print(datetime.now() - s)
#     #print(A)