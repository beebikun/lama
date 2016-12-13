# -*- coding: utf-8 -*-
import re
import datetime
import os
import time
import subprocess
import math
from sys import stdout

from lama.cleaner.config import BADS_SYMBOLS, TAGS, HEADERS, SYSTEM_NOISE


class Cleaner(object):
    TYPE = ''
    TAGS = {}
    HEADERS = []
    SYSTEM_NOISE = []

    _HTML_BADS = set()
    _UTF_BADS = set()

    _remove_bads_d = 0

    ORDER = [
        ('pre', 'proccess_items'),             # 0 a
        ('remove_bads', 'proccess_items'),     # 1 b
        ('remove_html', 'proccess_items'),     # 2 c
        ('remove_repeat', 'proccess_items'),   # 3 d
        ('concat', 'concat'),                  # 4 e
        ('remove_repeat', 'process_concated'), # 5 f
        ('remove_noise', 'process_concated'),  # 6 g
    ]

    def __init__(self, lama):
        self.lama = lama
        self.STORAGE = lama.create_storage(self.TYPE)
        for pattern, tag in TAGS.items():
            self.TAGS[pattern] = tag
        self.HEADERS += HEADERS
        self.SYSTEM_NOISE += SYSTEM_NOISE

    def remove_bads(self, text):
        for normal, bad_symbols in BADS_SYMBOLS.items():  # replace bad symbols
            for s in bad_symbols:
                text = text.replace(s, normal)

        entity_reg = re.compile('&#\w+;')
        bad_utf_reg = re.compile(r'[^\./# ?$,><@\w()\n&*\'"!%\-\[=+:;~\]\\|{}]+')
        entity = set(entity_reg.findall(text))
        if entity:
            text = entity_reg.sub('', text)
            self._HTML_BADS.update(entity)
        bad_utf = set(bad_utf_reg.findall(text))
        if bad_utf:
            text = bad_utf_reg.sub('', text)
            self._UTF_BADS.update(bad_utf)
        return text

    def remove_html(self, text, stoppattern=None):
        def replace(m):
            if stoppattern and stoppattern.search(m.group()):
                return m.group()
            return ''
        text = re.sub('<[\s\S]*?>', '', text)
        return text

    def strip(self, text):
        text = re.sub('&nbsp;|\t', ' ', text)  # remove html spaces
        text = re.sub(' {2,}', ' ', text)  # remove doubled spaces
        text, n = re.subn('^ ', '', text, flags=re.M)  # trail whitespaces
        text = re.sub(' $', '', text, flags=re.M)  # trail whitespaces
        text = re.sub('\n{2,}', '\n', text)  # remove empty strings
        # A&M is better than A & M
        text = text.replace(' &', '&').replace('& ', '&')
        text = text.replace(' ,', ',')
        return text.strip()

    def insert_tags(self, text):

        for pattern, tag in self.TAGS.iteritems():
            text, n = pattern.subn(tag, text)
        return text

    def remove_repeat(self, text):
        seen = set()
        strings = text.split('\n')
        uniq_strings = []

        for string in strings:
            s = string.strip().lower()
            if s not in seen:
                seen.add(s)
                uniq_strings.append(string)

        text = '\n'.join(uniq_strings)
        return text

    def remove_repeated_no_letters(self, text):
        def remove_repeated(m):
            p = m.group()
            p_set = set(p)
            if len(p_set) > 1:
                return p
            return ''.join(p_set)

        text = re.sub('[^\s\w]{2,}', remove_repeated, text)
        return text

    def remove_noise(self, text):
        for regex in self.SYSTEM_NOISE:
            text = regex.sub('', text)

        text = self.strip(text)
        text = self.remove_repeated_no_letters(text)

        for regex in self.HEADERS:
            # print ('------------')
            # print (regex.findall(text))
            # print (regex.pattern)
            text, n = regex.subn('', text)
            # print (n)
        return text

    def concat(self, *args):
        target_name = self.TARGET_STORAGE.generate_name(ftype=self.TYPE)
        output_path, exist = self.TARGET_STORAGE.join(target_name)
        output = open(output_path + 'ml', 'w+')
        source_path, exist = self.SOURCE_STORAGE.join('*')
        print('Start work with:{}'.format(source_path))
        subprocess.call('cat {} > {}'.format(source_path, output_path), shell=True)
        output.close()

    def get_source_text(self, storage=None):
        storage = storage or self.SOURCE_STORAGE
        source_files = storage.files(filtype=self.TYPE)
        filename = source_files[0]
        self.source_path = os.path.join(storage.STORAGE, filename)
        print('Start work with: {}'.format(filename))
        text = storage.read(filename)
        return text

    def pre(self, text):
        return text

    def process_concated(self, fn):
        source = self.get_source_text()
        text = fn(source)
        self.write(text)

    def proccess_items(self, fn):
        def log(i):
            d2 = datetime.datetime.now()
            spent = round((d2 - d1).seconds, 2)
            time_per_file = round(spent / float(i), 2)
            remining_time = round(time_per_file * (l - i), 2)
            percent = round(i * 100.0 / l, 2)
            stdout.write('\r{} %\t\tTime per file:{} sec\t\tRemining time: {} sec  '.format(
                percent, time_per_file, remining_time))
            stdout.flush()

        if self.N:
            self.START = int(self.N)
            self.END = self.START + 1
        files = self.SOURCE_STORAGE.files()
        end = self.END or len(files)
        l = end - self.START
        d1 = datetime.datetime.now()
        print('{} files for process'.format(end - self.START))
        for i, filename in enumerate(files[self.START:end]):
            text = self.SOURCE_STORAGE.read(filename)
            text = fn(text)
            if text is None:
                continue
            self.write(text, filename, ftype=False)
            log(i + 1)

        stdout.write("\n")

    def storage_name_by_order_idx(self, idx):
        if idx == 0:
            return 'raw'
        a = 97
        return chr(a + idx - 1)

    def write(self, text, name='all', concat=False, ftype=True):
        if text is None or isinstance(text, bool):
            return
        text = self.strip(text)
        return self.TARGET_STORAGE.write(text, name=name, ftype=ftype and self.TYPE, concat=concat)

    def clean(self, f=0, to=None, s=0, e=None, n=None):
        self.START = int(s)  # number of file to start
        self.END = e and int(e)  # number of file to stop
        self.N = n  # process only file with this number
        f = int(f or 0)
        to = min(int(to or f + 1), len(self.ORDER))
        while f < to:
            fn_name, process_fn = self.ORDER[f]
            source_name = self.storage_name_by_order_idx(f)
            target_name = self.storage_name_by_order_idx(f + 1)
            print('------------')
            d1 = datetime.datetime.now()
            print('Start cleaning: {} (stage {})'.format(fn_name, target_name))
            self.SOURCE_STORAGE = self.STORAGE.create_sub_storage(source_name)
            self.TARGET_STORAGE = self.STORAGE.create_sub_storage(target_name)
            self.EXT = target_name
            clean_fn = getattr(self, fn_name)
            process = getattr(self, process_fn)
            process(clean_fn)
            if fn_name == 'remove_bads':
                print(self._HTML_BADS)
                print(self._UTF_BADS)
            d2 = datetime.datetime.now()
            print('End cleaning: {} sec'.format((d2 - d1).seconds))
            time.sleep(.2)
            f += 1
        print('Files have been cleaned')

    def split(self, c=None, v=None, parts=None):
        """
        python run.py split wiki [-c num] [-v num] [-parts [percent, percent, ...]] [-type [a|b|c]]
        -c - count of files: it will be c files the same size
        -v - volume of filex: here will be x files with v strings in each
        -parts - split file to parts of given percentage. if sum of all percentage != 100, here will be one more file
        """
        stype = self.storage_name_by_order_idx(len(self.ORDER))
        self.EXT = stype
        self.SOURCE_STORAGE = self.STORAGE.create_sub_storage(stype)
        self.TARGET_STORAGE = self.SOURCE_STORAGE.create_sub_storage('parts')
        source = self.get_source_text()
        strings = source.split('\n')
        strings_count = len(strings)
        if parts is None:
            if v:
                c = round(strings_count / float(v))
            if c:
                percentage = 100 / float(c)
            else:
                return self.lama.help()
            c = int(c)
            parts = [percentage] * c
        else:
            parts = [int(p) for p in parts.split(',')]
            c = len(parts)
        total_percentage = sum(parts)
        if total_percentage < 100:
            parts.append(100 - total_percentage)
        elif total_percentage > 100:
            while True:
                parts.pop()
                total_percentage = sum(parts)
                diff = total_percentage - 100
                if diff <= 0:
                    if diff < 0:
                        parts.append(diff * -1)
                    break

        chunks = [int(math.ceil(strings_count * p / 100.0)) for p in parts]
        parts_paths = []
        for i, ch in enumerate(chunks):
            strings_before = sum(chunks[:i])
            ch_strings = strings[strings_before: strings_before + ch]
            path = self.write('\n'.join(ch_strings), name='p{}from{}'.format(i + 1, c), concat=True)
            parts_paths.append(path)
        data = {'source': self.source_path, 'parts': parts_paths}
        print(data)
        return data
