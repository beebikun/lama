# -*- coding: utf-8 -*-
from lama.cleaner import Cleaner
import re


class SecCleaner(Cleaner):
    TYPE = 'sec'

    def pre(self, item, text):
        text = re.sub('<SEC-HEADER>[\s\S]+</SEC-HEADER>', '', text, flags=re.I)
        text = re.sub('<DOCUMENT>\n<TYPE>GRAPHIC[\s\S]+</DOCUMENT>', '', text, flags=re.I)
        return text


cleaner = SecCleaner
