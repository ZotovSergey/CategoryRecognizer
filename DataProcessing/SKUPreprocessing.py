import pandas as pd

def clear_sku(sku_rows):
    cleaned_sku_rows = sku_rows.str.replace(r'\s{2,}', ' ')
    cleaned_sku_rows = cleaned_sku_rows.str.replace.str.replace(r'^\[[^\[\]]*\]|^{[^{}]*}|^<[^<>]*>|~|^#|^\'|^\?|^\*|^\.|^\,|^_|^-|^–|{|}', '')
    return cleaned_sku_rows


class SKUReader:

    def __init__(self, sku_sheet_name, sku_col_title='SKU'):
        self.sku_sheet_name = sku_sheet_name
        self.sku_col_title = sku_col_title

    def get_sku_from_excel(self, file_path):
        initial_rows = pd.read_excel(file_path, sheet_name=self.sku_sheet_name, usecols=[self.sku_col_title], squeeze=True)
        preprocessed_rows = list(' ' + initial_rows.str.upper() + ' ')
        return preprocessed_rows, list(initial_rows)