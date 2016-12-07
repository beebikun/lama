# -*- coding: utf-8 -*-
from lama.cleaner import Cleaner
import re


class SecCleaner(Cleaner):
    TYPE = 'sec'

    def clean_raw_item_2(self, item, text):
        text = self.remove_html()
        return text


cleaner = SecCleaner
