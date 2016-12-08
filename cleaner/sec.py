# -*- coding: utf-8 -*-
from lama.cleaner import Cleaner
import re

date_regex = re.compile(r'SUBJECT.TO.COMPLETION.*DATED.(\w+.\d+, ?\d+)')


class SecCleaner(Cleaner):
    TYPE = 'sec'

    PAGE_SPLITS = [
        '<hr[^>]*?>',
        '------------',
    ]

    def pre(self, text):
        text = re.sub('<SEC-HEADER>[\s\S]+</SEC-HEADER>', '', text, flags=re.I)
        # text = re.sub('<DOCUMENT>\n<TYPE>GRAPHIC[\s\S]+</DOCUMENT>', '', text, flags=re.I)
        s4documents = text.split('<DOCUMENT>')
        # text = re.sub('<DOCUMENT>\n<TYPE>S-4[\s\S]+?</DOCUMENT>', '', text, flags=re.I)
        s4 = []
        for form in s4documents:
            if '<TYPE>S-4' not in form:
                continue
            form = form.split('TEXT>')[1][:-2]
            pages = re.split('|'.join(self.PAGE_SPLITS), form, flags=re.I)
            # i_start = 0
            i_end = len(pages)
            i = -1
            for page in pages:
                i += 1
                if getattr(self, 'date', None) is None:
                    date = date_regex.findall(page)
                    if len(date):
                        i_start = i
                        continue
                if re.search('INFORMATION NOT REQUIRED IN PROSPECTUS', page):
                    i_end = i
                    break
                elif re.search(r'SIGNATURES', page) and \
                        re.search(r'the requirements of the Securities Act', page, flags=re.I):
                    i_end = i
                    break
            html = ''.join(pages[i_start + 1:i_end - 1])
            print ([i_end, len(pages)])
            s4.append(html)
        # s4.append(text)
        text = '\n'.join(s4)
        # text = self.remove_html(text)
        return text


cleaner = SecCleaner
