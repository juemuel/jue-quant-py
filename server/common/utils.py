# common/utils.py
def format_number(num_str):
    if '万' in num_str:
        return float(num_str.replace('万', '')) * 10000
    elif '亿' in num_str:
        return float(num_str.replace('亿', '')) * 100000000
    else:
        return float(num_str)

def format_stock_code(code):
    return str(code).zfill(6)
