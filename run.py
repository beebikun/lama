# -*- coding: utf-8 -*-
import os
import datetime
import pickle
# from collections import Counter
import re
from pymongo import MongoClient
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LAMEDOCK_ROOT = os.path.dirname(PROJECT_ROOT)
STORAGE_ROOT = os.path.join(LAMEDOCK_ROOT, 'texts')

sys.path.append(os.path.dirname(PROJECT_ROOT))


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


class Storage():
    DATE_FORMAT = '%d%m%y-%H%M'

    def __init__(self, dir_name, parent_folder=None):
        if parent_folder is None:
            parent_folder = STORAGE_ROOT
        self.STORAGE, exists = self._check_exists(dir_name, parent_folder, create=True)

    def create_sub_storage(self, subfolder, date=True):
        parent = self.STORAGE
        # if date:
        #     parent, exists = self._check_exists(subfolder, create=True)
        #     subfolder = datetime.datetime.now().strftime('%d%m%y-%H%M')
        return Storage(subfolder, parent)

    def _check_exists(self, subfolder, folder=None, create=False):
        if folder is None:
            folder = self.STORAGE
        path = os.path.join(folder, subfolder)
        exists = False
        if not os.path.exists(path):
            if create:
                os.makedirs(path)
        else:
            exists = True
        return path, exists

    def generate_name(self, name, ext, ftype, text=None):
        wc = ''
        if text:
            words = re.findall('\w+', text.lower())
            wc = str(len(set(words)))
        date = datetime.datetime.now().strftime(self.DATE_FORMAT)
        return '{ftype}_{name}_{wc}_{date}.c{ext}'.format(
            ftype=ftype, name=name, wc=wc, date=date, ext=ext)

    def write(self, text, name='all', ftype=None, ext=None, rewrite=True):
        def write(text, line_mode='ml'):
            if line_mode == 'sl':
                text = text.replace('\n', ' ')
            f = open(file_path + line_mode, 'w+')
            f.write(text)
            f.close()
        if ext:
            name = self.generate_name(name, ext, ftype, text)
        file_path, exists = self._check_exists(name)
        if not rewrite and exists:
            raise ValueError('File {} already exists'.format(file_path))
        write(text)
        if name != 'all':
            write(text, 'sl')
        print 'Write file {}'.format(file_path)
        return file_path

    def write_pickle(self, data, name='all', ftype=None, ext=None):
        name = self.generate_name(name, ext, ftype)
        filepath, exists = self._check_exists(name)
        f = open(filepath, 'wb')
        pickle.dump(data, f)
        f.close()
        return filepath

    def read_pickle(self, name='all', ftype=None, ext=None):
        name = self.generate_name(name, ext, ftype)
        filepath, exists = self._check_exists(name)
        f = open(filepath, 'rb')
        data = pickle.load(f)
        f.close()
        return data

    def read(self, name):
        file_path, exists = self._check_exists(name, create=False)
        if not exists:
            raise ValueError('File {} is not exist'.format(file_path))
        f = open(file_path, 'r+')
        text = f.read()
        f.close()
        return text

    def files(self, filtype=None):
        def get_date(filename):
            filename = filename.split('.')[0]
            date = filename.split('_')[-1]
            return datetime.datetime.strptime(date, self.DATE_FORMAT)
        files = []
        for f in os.listdir(self.STORAGE):
            if os.path.isfile(os.path.join(self.STORAGE, f)):
                if filtype and not f.startswith(filtype):
                    continue
                files.append(f)
        if filtype:
            return sorted(files,
                          key=get_date, reverse=True)
        return files


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
        return Storage(subfolder)

    def help(self):
        print """
        usage
        pythin run.py lich wiki
        -----------------------------------
        python run.py clean wiki -f [raw|a|b] [-to [a|b|c]] [-s num] [-e num]
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
        raise SystemExit()


lama = Lama()

from lama.lich import wiki as wiki_lich
from lama.cleaner import wiki as wiki_cleaner
# print dir(luwak)

CLEAN = {
    'wiki': wiki_cleaner.process,
}


DOWNLOAD = {
    'wiki': wiki_lich.download,
    # 'sec': lich.sec.download,
}

"""
usage
pythin run.py lich wiki
-----------------------------------
python run.py clean wiki -f [raw|a|b] [-to [a|b|c]] [-s num] [-e num]
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


if __name__ == '__main__':
    d1 = datetime.datetime.now()
    print_help = len(sys.argv) < 2 or sys.argv[1] == 'help'

    if print_help:
        lama.help()

    action = sys.argv[1]
    name = sys.argv[2]

    kwargs = dict([a.strip().split(' ') for a in ' '.join(sys.argv[3:]).split('-') if a])

    if action == 'clean':
        CLEAN[name](lama, **kwargs)

    if action == 'lich':
        DOWNLOAD[name](lama)

    if action == 'split':
        kwargs['split'] = True
        CLEAN[name](lama, **kwargs)

    d2 = datetime.datetime.now()
    print 'Spended time was {} sec'.format((d2 - d1).seconds)
