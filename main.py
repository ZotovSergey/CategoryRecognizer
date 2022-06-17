import multiprocessing as mp

from GUI.GUI import run_app

if __name__== "__main__":
    # Для того, чтобы exe-файл работал в Windows
    mp.freeze_support()
    # Запуск окна приложения
    run_app()