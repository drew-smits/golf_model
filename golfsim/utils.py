import json
import requests
import re
from datetime import date, timedelta
import numpy as np

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


class File:
    def __init__(self, filename):
        self.filename = filename


class JsonFile(File):
    baseURL = ''
    jsonStart = ''
    jsonEnd = ''

    fileExtension = '.json'

    def __init__(self, filename):
        super().__init__(filename)
        self.data = None
        try:
            self.read()
        except FileNotFoundError:
            print('File Not Found:', filename)
            pass

    def read(self):
        with open(self.filename, 'r') as f:
            self.data = json.load(f)

    def update(self, suffix='', cookie={}):
        data = self.parse(requests.get(self.baseURL + suffix, cookies=cookie).text)
        self.data = self.parseJson(data)
        self.write()

    def parse(self, text):
        return json.loads(getSubstringFromIdentifiers(text, self.jsonStart, self.jsonEnd))

    def parseJson(self, data):
        return data

    def write(self):
        with open(self.filename, 'w+') as f:
            json.dump(self.data, f)


class TextFile(File):
    fileExtension = '.txt'

    def __init__(self, filename):
        super().__init__(filename)
        self.text = None

    def read(self):
        with open(self.filename, 'r') as f:
            self.text = f.read()

    def write(self):
        with open(self.filename, 'w+') as f:
            f.write(self.text)


def normalize(arr, dims=None):
    # if dims is None:
    #     dims = [0]
    # for i in dims:
    #     arr[:, i] = arr[:, i] / sum(arr[:, i])
    arr[:] = arr[:] / sum(arr[:])

def inverseAgeDecay(arr, exp, offset, dims=None):
    # if dims is None:
    #     dims = [0]
    # for i in dims:
    #     arr[:, i] = (arr[:, i] + offset) ** -exp
    arr[:] = (arr[:] + offset) ** -exp


def calcPlayerSkill(tsgs, dates, decayFunc, *args):
    sd = np.std(tsgs)
    decayFunc(dates, *args)
    normalize(dates)
    tsgs = tsgs * dates
    return sum(tsgs), sd


def getSubstringFromIdentifiers(string, startID, endID):
    try:
        startIdx = string.index(startID) + len(startID)
        endIdx = string.index(endID, startIdx)
    except ValueError:
        return ''
    if startIdx >= 0 and endIdx >= 0:
        return string[startIdx:endIdx]
    return ''


def alphanum_key(string):
    """
    Return a list of strings and numbers from the input string.
    This allows numeric strings to be sorted correctly.
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', string)]


def text_date_to_int(text):
    month = str(months.index(text[0:3]) + 1)
    if len(month) == 1:
        month = '0' + month
    day = text[4:text.index(',')]
    if len(day) == 1:
        day = '0' + day
    year = text[-4:]

    return int(year + month + day)


def get_age_int_date(old_date, new_date):
    old_date = date(int(str(old_date)[:4]), int(str(old_date)[4:6]), int(str(old_date)[6:]))
    new_date = date(int(str(new_date)[:4]), int(str(new_date)[4:6]), int(str(new_date)[6:]))
    return (new_date - old_date).days


def date_to_int(d):
    return int(str(d).replace('-', ''))


def int_to_date(d):
    return date(int(str(d[:4])), int(str(d[4:6])), int(str(d[6:])))


def get_earliest_int_date(compare_date, days_before):
    return date_to_int(compare_date - timedelta(days=days_before))


def dollars_to_int(dollars):
    cleaned = dollars.replace('$', '').replace(',', '')
    parts = cleaned.split('.')
    try:
        return int(parts[0])
    except ValueError:
        return parts[0]


class CustomError(Exception):
    pass


class ResponseErrorHTTP(CustomError):
    pass
