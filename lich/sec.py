# -*- coding: utf-8 -*-
from lama.lich import Lich
import re
import datetime
from sys import stdout


class SecLich(Lich):
    TYPE = 'sec'
    BASE_URL = "ftp://ftp.sec.gov"

    def convert_idxs(self, **kwargs):
        SOURCE = self.STORAGE.create_sub_storage('indexes')
        TARGET = self.STORAGE.create_sub_storage('urls')
        indexes = SOURCE.files()
        created_urls = TARGET.files()
        for idx_name in indexes:
            urls = []
            if idx_name in created_urls:
                continue
            idx = SOURCE.read(idx_name)
            for line in idx.split('\n'):
                if 's-4' not in line.lower():
                    continue
                path = re.search('edgar/data/[^\s]+', line).group()
                url = '{}/{}'.format(self.BASE_URL, path)
                urls.append(url)
            if len(urls) > 0:
                try:
                    TARGET.write('\n'.join(urls), idx_name)
                    print('Write urls for {}'.format(idx_name))
                except Exception as e:
                    print('Failed write urls for {}'.format(idx_name))
                    raise e
            else:
                print('File {} has no S-4'.format(idx_name))

    def download(self, **kwargs):
        def log(i):
            d2 = datetime.datetime.now()
            spent = round((d2 - d1).seconds, 2)
            time_per_file = round(spent / float(i), 2)
            remining_time = round(time_per_file * (l - i), 2)
            percent = round(i * 100.0 / l, 2)
            stdout.write('\r{} %\t\tTime per file:{} sec\t\tRemining time: {} sec  '.format(
                percent, time_per_file, remining_time))
            stdout.flush()

        d1 = datetime.datetime.now()
        SOURCE = self.STORAGE.create_sub_storage('urls')
        url_files = SOURCE.files()
        for filename in url_files:
            urls = SOURCE.read(filename).split('\n')
            l = len(urls)
            for i, url in enumerate(urls):
                self.wget(url)
                log(i + 1)
            stdout.write('\n')
            print('Urls for {} have been downloaded'.format(filename))
            break

lich = SecLich
