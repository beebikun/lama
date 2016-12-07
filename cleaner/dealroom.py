# -*- coding: utf-8 -*-
from lama.cleaner import Cleaner


class DealRoomCleaner(Cleaner):
    TYPE = 'dealroom'

    def pickle(self, **kwargs):
        storage = self.STORAGE.create_sub_storage('data')
        for filename in storage.files():
            if filename.startswith('.'):
                continue
            requests = []
            data = storage.read(filename).split('-------------')
            for r in data:
                if not r.strip():
                    continue
                r = [i for i in r.split('\n') if i.strip()]
                cat = r[0]
                assert cat
                text = '\n'.join(r[1:]).decode('utf-8', errors='replace').encode('ascii', errors='ignore')
                if not text:
                    print(r)
                assert text
                requests.append({
                    'cat': cat.replace('Cat:', '').strip(),
                    'text': text.strip(),
                })
            storage.write_pickle(requests, name=filename.replace(' ', ''), ext='', ftype='requests')


cleaner = DealRoomCleaner
