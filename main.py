import multiprocessing as mp

from gui.GUI import run_app

import pandas as pd
#from DataProcessing.SKUPreprocessing import clean_sku_df, main_clear

if __name__== "__main__":
    # Для того, чтобы exe-файл работал в Windows
    mp.freeze_support()
    # Запуск окна приложения
    run_app()
