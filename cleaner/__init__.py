# -*- coding: utf-8 -*-
import re
import datetime
import os
import time
import math
from sys import stdout

from lama.cleaner.config import BADS_SYMBOLS, TAGS, HEADERS, SYSTEM_NOISE


class Cleaner(object):
    TYPE = ''
    TAGS = {}
    HEADERS = []
    SYSTEM_NOISE = []
    maxN = None

    _HTML_BADS = set()
    _UTF_BADS = set()

    ORDER = ['raw', 'a', 'b', 'c']

    _remove_bads_d = 0

    def __init__(self, lama):
        self.lama = lama
        self.STORAGE = lama.create_storage(self.TYPE)
        self.TAGS.update(**TAGS)
        self.HEADERS += HEADERS
        self.SYSTEM_NOISE += SYSTEM_NOISE
        self.NOISE = self.HEADERS + self.SYSTEM_NOISE
        # self.items = self.lama.db_items.find_all({'type': self.TYPE})

    def remove_bads(self, text):
        d1 = datetime.datetime.now()
        for normal, regex in BADS_SYMBOLS.iteritems():  # replace bad symbols
            text = regex.sub(normal, text)

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
        d2 = datetime.datetime.now()
        self._remove_bads_d += (d2 - d1).seconds
        return text

    def remove_html(self, text, stoppattern=None):
        def replace(m):
            if stoppattern and stoppattern.search(m.group()):
                return m.group()
            return ''

        text = re.sub('<[\s\S]*?>', replace, text)
        return text

    def strip(self, text):
        d1 = datetime.datetime.now()
        text = re.sub('&nbsp;|\t', ' ', text)  # remove html spaces
        text = re.sub(' {2,}', ' ', text)  # remove doubled spaces
        text, n = re.subn('^ ', '', text, flags=re.M)  # trail whitespaces
        text = re.sub(' $', '', text, flags=re.M)  # trail whitespaces
        text = re.sub('\n{2,}', '\n', text)  # remove empty strings
        # A&M is better than A & M
        text = text.replace(' &', '&').replace('& ', '&')
        d2 = datetime.datetime.now()
        print 'Strip: {} sec'.format((d2 - d1).seconds)
        return text.strip()

    def insert_tags(self, text):
        d1 = datetime.datetime.now()
        for pattern, tag in self.TAGS.iteritems():
            text, n = pattern.subn(tag, text)
            print 'Insert {} tags for pattern {}'.format(n, tag)
        d2 = datetime.datetime.now()
        print 'Insert tags: {} sec'.format((d2 - d1).seconds)
        return text

    def remove_repeat(self, text):
        d1 = datetime.datetime.now()
        seen = set()
        seen_add = seen.add
        strings = text.split('\n')
        print 'All strings: {}'.format(str(len(strings)))
        uniq_strings = [string.strip() for string in strings
                        if not (string.strip() in seen or seen_add(string.strip()))]
        print 'Uniq strings: {}'.format(str(len(uniq_strings)))
        text = '\n'.join(uniq_strings)
        d2 = datetime.datetime.now()
        print 'Remove repeated strings: {} sec'.format((d2 - d1).seconds)
        return text

    def remove_noise(self, text):
        d1 = datetime.datetime.now()
        for regex in self.NOISE:
            ds = datetime.datetime.now()
            print regex.pattern
            text, n = regex.subn('', text)
            de = datetime.datetime.now()
            print 'Noise for pattern: {} sec. Found {}'.format((de - ds).seconds, n)
        d2 = datetime.datetime.now()
        print 'Remove noises: {} sec'.format((d2 - d1).seconds)
        return text

    def get_source_text(self):
        source_files = self.SOURCE_STORAGE.files(filtype=self.TYPE)
        filename = source_files[0]
        d1 = datetime.datetime.now()
        self.source_path = os.path.join(self.SOURCE_STORAGE.STORAGE, filename)
        print 'Start work with file: {}'.format(self.source_path)
        text = self.SOURCE_STORAGE.read(filename)
        d2 = datetime.datetime.now()
        print 'Load file: {} sec'.format((d2 - d1).seconds)
        # text = self.strip(text)
        return text

    def clean_b(self):
        # output: b - insert tags, no repeated strings
        print 'Clean: from B to C'
        text = self.get_source_text()
        text = self.insert_tags(text)
        text = self.remove_noise(text)
        self.write(text)

    def clean_a(self):
        # output: b - no headers, no repeated strings, no stop-symbols
        print 'Clean: from A to B'
        text = self.get_source_text()
        text = self.remove_noise(text)
        self.write(text, ext='b')

    def _page_header(self, filename, text, item, i):
        return '----------TITLE:{}|{}|{}-----------\n'.format(
            self.START + i + 1, item['title'].encode('utf8'), filename
        ) + text

    def clean_raw(self):
        # output: a - no inner noise
        print 'Clean: from RAW to A'
        files = self.SOURCE_STORAGE.files()
        end = self.END or len(files)
        l = end - self.START
        all_texts = []
        all_meta = []
        d1 = datetime.datetime.now()
        for i, filename in enumerate(files[self.START:self.END]):
            stdout.flush()
            text = self.SOURCE_STORAGE.read(filename)
            item = self.lama.db_items.items.find_one({'name': filename})
            text = self.remove_bads(text)
            text, meta = self.clean_raw_item(item, text)
            if text is None:
                continue
            # text = self._page_header(filename, text, item, i)
            all_texts.append(text)
            all_meta.append(meta)
            d2 = datetime.datetime.now()
            spent = (d2 - d1).seconds
            time_per_file = round(spent / float(i + 1), 2)
            remining_time = time_per_file * (l - i)
            percent = round(i * 100.0 / l, 3)
            stdout.write('\r{} %\tTime per file:{} sec\tRemining time: {} sec'.format(
                percent, time_per_file, remining_time))
        stdout.write("\n")
        print 'Remove bads: {} sec'.format(self._remove_bads_d)

        all_texts = '\n'.join(all_texts)
        self.TARGET_STORAGE.write_pickle(all_meta, ext='ameta', ftype=self.TYPE)
        print 'The following bads have been found:'
        print self._HTML_BADS
        print ' '.join(self._UTF_BADS)
        self.write(all_texts)

    def write(self, text, name='all'):
        text = self.strip(text)
        text = self.remove_repeat(text)
        return self.TARGET_STORAGE.write(text, name=name, ext=self.EXT, ftype=self.TYPE)
        # self.TARGET_STORAGE.write(text.replace('\n', ' '), name=name, ext='{}sl'.format(ext), ftype=self.TYPE)

    def run(self, f='raw', to=None, s=0, e=None):
        self.START = int(s)
        self.END = e and int(e)
        si = self.ORDER.index(f)
        ei = self.ORDER.index(to) if to else si + 1
        for i, name in enumerate(self.ORDER[si:ei]):
            target = self.ORDER[i + 1]
            self.SOURCE_STORAGE = self.STORAGE.create_sub_storage(name)
            self.TARGET_STORAGE = self.STORAGE.create_sub_storage(target)
            self.EXT = target
            getattr(self, 'clean_' + name)()
            time.sleep(.2)
        print 'Files have been cleaned'

    def split(self, c=None, v=None, parts=None, stype=None):
        """
        python run.py split wiki [-c num] [-v num] [-parts [percent, percent, ...]] [-type [a|b|c]]
        -c - count of files: it will be c files the same size
        -v - volume of filex: here will be x files with v strings in each
        -parts - split file to parts of given percentage. if sum of all percentage != 100, here will be one more file
        -stype - source type of file to split. default 'c'
        """
        if stype is None:
            stype = self.ORDER[-1]
        if stype not in self.ORDER[1:]:
            return self.lama.help()
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
            path = self.write('\n'.join(ch_strings), name='p{}from{}'.format(i + 1, c))
            parts_paths.append(path)
        data = {'source': self.source_path, 'parts': parts_paths}
        print data