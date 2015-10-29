import re


def byteify(input_str):
    if isinstance(input_str, dict):
        return {byteify(key): byteify(value) for key, value in input_str.iteritems()}
    elif isinstance(input_str, list):
        return [byteify(element) for element in input_str]
    elif isinstance(input_str, unicode):
        return input_str.encode('utf-8')
    else:
        return input_str


def fix_output(json_to_fix):
    first_pass = re.sub('(\w+:)(\d+\.?\d*)', r'\1"\2"', json_to_fix)
    second_pass = re.sub('(\w+):', r'"\1":', first_pass)
    return second_pass


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def return_as_number(s):
    if is_number(s):
        return float(s)
    else:
        return 0.00
