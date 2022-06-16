import multiprocessing as mp

from datetime import datetime

from GUI.GUI import run_app
from DataProcessing.DataProcessing import BrendRecognizer
from BrendDictionary.BrendDictionary import BrendDictionary, find_all_dict, load_dictionary

from DataProcessing.SKUPreprocessing import SKUReader


if __name__== "__main__":
    run_app()