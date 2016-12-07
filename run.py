# -*- coding: utf-8 -*-
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LAMEDOCK_ROOT = os.path.dirname(PROJECT_ROOT)
STORAGE_ROOT = os.path.join(LAMEDOCK_ROOT, 'texts')

sys.path.append(os.path.dirname(PROJECT_ROOT))


from pymongo import MongoClient

from lama.storage import Storage

help_output = """
    usage
    pythin run.py wiki lich
    -----------------------------------
    python run.py wiki clean -f [raw|a|b] [-to [a|b|c]] [-s num] [-e num]
    where:
    -f - from format
    -to - to format
    -s - num of file to start
    -e - num of file to end

    clean level:
    a - no inner noise
    b - no headers, no repeated
    c - insert tags, no repeated
    -----------------------------------
    python run.py split wiki [-c num] [-v num] [-parts percent,percent,...] [-type [a|b|c]]
    -c - count of files: it will be c files the same size
    -v - volume of filex: here will be x files with v strings in each
    -parts - split file to parts of given percentage. if sum of all percentage != 100, here will be one more file
    -stype - source type of file to split. default c
    """


class DBCollection(object):
    def __init__(self, db, collection_name):
        self.items = db[collection_name]

    def write(self, item):
        _id = self.items.insert(item)
        return self.items.find_one({'_id': _id})

    def check(self, name=None, query=None):
        if query is None:
            query = {'name': name}
        return self.items.find_one(query)

    def find_all(self, query):
        return self.items.find(query)

    def get_or_create(self, item, query=None):
        in_db = self.check(item.get('name'), query)
        return in_db or self.write(item)

    def update(self, data, name=None, query=None):
        if query is None:
            query = {'name': name}
        self.items.update(query, {'$set': data})


class Lama(object):
    DB_NAME = 'lama'
    DB_COLLECTION = 'html_items'
    client = MongoClient('localhost', 27017)
    db = client[DB_NAME]

    def __init__(self):
        """ item in db_items:
         - name
         - url
         - file_path
        """
        self.db_items = self.create_collection(self.DB_COLLECTION)

    def create_collection(self, collection_name):
        return DBCollection(self.db, collection_name)

    def create_storage(self, subfolder):
        return Storage(subfolder, STORAGE_ROOT)

    def help(self):
        print(help_output)
        raise SystemExit()


lama = Lama()

from lama.lich import wiki as wiki_lich
from lama.cleaner import (
    wiki as wiki_cleaner,
    dealroom as dealroom_cleaner,
    sec as sec_cleaner,
)

CLEAN = {
    'wiki': wiki_cleaner.cleaner,
    'dealroom': dealroom_cleaner.cleaner,
    'sec': sec_cleaner.cleaner,
}


DOWNLOAD = {
    'wiki': wiki_lich.download,
    # 'sec': lich.sec.download,
}


import datetime

if __name__ == '__main__':
    d1 = datetime.datetime.now()
    print_help = len(sys.argv) < 2 or sys.argv[1] == 'help'

    if print_help:
        lama.help()

    name = sys.argv[1]
    action = sys.argv[2]

    kwargs = dict([a.strip().split(' ') for a in ' '.join(sys.argv[3:]).split('-') if a])

    if action == 'lich':
        DOWNLOAD[name](lama)

    else:
        cleaner = CLEAN[name](lama)
        getattr(cleaner, action)(**kwargs)

    d2 = datetime.datetime.now()
    print('Spended time was {} sec'.format((d2 - d1).seconds))
