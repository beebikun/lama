import hashlib
import subprocess
import urllib
import json
import time
import os
FNULL = open(os.devnull, 'w')


class Lich(object):
    TYPE = ''

    def __init__(self, lama):
        self.lama = lama
        self.STORAGE = lama.create_storage(self.TYPE)
        self.RAW_STORAGE = self.STORAGE.create_sub_storage('raw')

    def get_name(self, url):
        return hashlib.sha224(url.encode('utf-8')).hexdigest()

    def wget(self, url, path=None, rewrite=False):
        if path is None:
            name = self.get_name(url)
            path, exists = self.RAW_STORAGE.join(name)
            if not rewrite and exists:
                print('File for url {} ({}) is already downloaded'.format(url, path))
                return
        subprocess.call(['wget', url, '-O', path], stdout=FNULL, stderr=subprocess.STDOUT)

    def get_json(self, url):
        response = urllib.urlopen(url)
        try:
            data = json.loads(response.read())
            time.sleep(.5)
        except Exception as e:
            print(url)
            print(response.read())
            raise e
        return data

    def write(self, item):
        item['name'] = self.get_name(item['url'])
        text = item.pop('text')
        item['file_path'] = self.STORAGE.write(text, item['name'], self.subfolder)
        self.lama.db_items.get_or_create(item)

    def run(self):
        pass
