# -*- coding: utf-8 -*-
from lama.cleaner import Cleaner
from lama.cleaner.wiki_categories import categories as allowed_categories
import re


class WikiCleaner(Cleaner):
    TYPE = 'wiki'
    TAGS = {
        re.compile('<math[\s\S]*?>([\s\S]*?)</math>'): '{MATH}',
    }
    HEADERS = [
        re.compile('^=+[\s\S]*?=+$', flags=re.M),
    ]
    SYSTEM_NOISE = [
        re.compile('\[{URL}[\s\S]*?\]'),
        re.compile('\[[^\]]*?{URL}\]'),
        re.compile('^[^\n]*?File:[^\n]*?$', flags=re.M),
        re.compile('^\|[^\n]*?$', flags=re.M),
    ]

    def collect(self, text, pattern):
        arr = []

        def replace(m):
            match = m.groups()[0]
            for r in match.split('\n'):
                r = r.replace('|', '').replace('*', '')
                arr.append(r.strip())
            return ''

        text = re.sub(pattern, replace, text)
        return text, arr

    def collect_under_header(self, text, header):
        pattern = '(?<==%s==\n)([\s\S]+?)(?===|$)' % header
        return self.collect(text, pattern)

    def collect_related(self, text):
        related = []

        def replace(m):
            title, text = m.groups()
            r = {'title': title}
            r['text'] = text or r['title']
            related.append(r)
            return r['text']

        text = re.sub('\[\[([^|\]]+)\|?([^|\]]+)?\]\]', replace, text)
        text = re.sub('{{see also\|([\s\S]*?)()}}', replace, text, flags=re.I)
        text = re.sub('{{Main\|([\s\S]*?)()}}', replace, text, flags=re.I)
        text = re.sub('{{Main article\|([\s\S]*?)()}}', replace, text, flags=re.I)
        text, see_also = self.collect_under_header(text, 'See also')  # see also category
        related += [{'title': r, 'text': r} for r in see_also]
        return text, related

    def collect_refs(self, text):
        text, refs = self.collect(text, '<ref[^>/]*?>([\w\W]*?)</ref>')  # inline refs
        text = re.sub('<ref [\s\S]*?/>', '', text)  # <ref /> without content
        text, add_refs = self.collect_under_header(text, 'References')  # referencies category
        return text, refs

    def clean_converts(self, text):
        def replace(m):
            r = m.groups()[0]
            num = re.search('\d+', r)
            val = re.search('[a-zA-Z]+', r)
            num = num.group() if num else ''
            val = val.group() if val else ''
            return '{}{}{}'.format(num, ' ' if num else '', val)

        text = re.sub('{{convert([\s\S]*?)}}', replace, text)
        return text

    def clean_recusive(self, text, regex):
        text, n = regex.subn('', text)
        if n:
            return self.clean_recusive(text, regex)
        return text

    def clean_system(self, text):
        text = text.replace("'''", "").replace("''", "")
        text = re.sub('<gallery[\s\S]*?>[\s\S]*?</gallery>', '', text)
        text = re.sub('<!--[\s\S]*?-->', '', text)  # comments
        text = re.sub('^#REDIRECT[\s\S]*?$', '', text, flags=re.I | re.M)
        text = self.clean_recusive(text, re.compile('{[^{}]*?}'))
        text = re.sub('\[\[[^\]]*?\]\]', '', text, flags=re.I)

        return text

    def bad_title(self, title):
        BADS = [
            '^User talk:',
            '^Template:',
            '^File:',
            '^User:',
            '^Portal:',
            '^Draft:',
            '^User:',
            '^Wikipedia:',
            '^List of',
        ]
        return re.search('|'.join(BADS), title)

    def bad_categories(self, categories):
        if re.search('film|(?:video game)', ' '.join(categories), flags=re.I):
            return True
        for category in categories:
            if category in allowed_categories:
                return False
        return True

    def remove_lists(self, text):
        def replace(m):
            header = m.group().split('\n')[0]
            return '{}\n{}'.format(header, '=' if m.group().endswith('=') else '')

        marker = '(?:\*|#|:|;|\-|(?:\d\.)|(?:[a-z]\.))+'
        text = re.sub('=+[\w ]+=+\n+(?:%s[^\n]*\n+)+=?' % marker, replace, text)  # sections with list only
        text = re.sub('(?:%s[^\n]*\n){4,}' % marker, '', text)
        return text

    def clean_raw_item_2(self, item, text):
        title = item['title']
        if self.bad_title(title):
            return None, None
        meta = {}
        meta['title'] = title
        meta['pageid'] = item['pageid']
        text, meta['categories'] = self.collect(text, '\[\[(Category:[\s\S]*?)\]\]')
        if self.bad_categories(meta['categories']):
            return None, None
        # if ':' in title:
        #     print title

        text = text.replace('== ', '==').replace(' ==', '==')
        text = self.clean_converts(text)

        text, meta['external_links'] = self.collect_under_header(text, 'External links')
        text, meta['further_reading'] = self.collect_under_header(text, 'Further reading')
        text, meta['notes'] = self.collect_under_header(text, 'Notes')
        text, meta['books'] = self.collect_under_header(text, 'Books')
        text, meta['papers'] = self.collect_under_header(text, 'Papers')
        text, meta['off_sites'] = self.collect_under_header(text, 'Official sites')
        # text, pops = self.collect_under_header(text, 'In popular culture')
        text, meta['related'] = self.collect_related(text)  # links in text
        text, meta['refs'] = self.collect_refs(text)
        text = self.clean_system(text)
        text = self.remove_lists(text)
        text = self.remove_html(text, re.compile('math'))
        return text, meta


cleaner = WikiCleaner
