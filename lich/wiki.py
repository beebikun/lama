# -*- coding: utf-8 -*-
from lama.lich import Lich

page_url = 'https://en.wikipedia.org/wiki/{}'

base_url = 'https://en.wikipedia.org/w/api.php?'

subcat_and_pages_url = base_url + 'action=query&format=json&' + \
                                  'list=categorymembers&cmlimit=max&' + \
                                  'cmtitle={}'
page_content_url = base_url + 'action=query&format=json&' + \
                              'prop=revisions%7Ccategories&iwurl=1&' + \
                              'clshow=!hidden&cllimit=max&rvprop=content&' + \
                              'pageids={}'


root_categories = [
    # 'Category:Corporate_finance',
    'Category:Financial_risk',
    # 'Category:Financial_problems',
    'Category:Economy',
    # 'Category:Finance',
]


class WikiLich(Lich):
    subfolder = 'wiki'
    N = 4

    def __init__(self, lama):
        super(WikiLich, self).__init__(lama)
        self.db_items = lama.create_collection('wiki_items')
        self.categories_list = lama.create_collection('categories_list')

    def done_dbelement(self, pageid=None, title=None):
        q = {'pageid': pageid} if pageid else {'title': title}
        self.db_items.update(q, {'$set': {'done': True}})

    def check_is_done(self, pageid=None, title=None):
        q = {'pageid': pageid} if pageid else {'title': title}
        q['done'] = True
        return self.db_items.check(query=q)

    def add_path(self, path, title):
        q = {'title': title}
        cat = self.categories_list.get_or_create(q, q)
        cat['paths'] = cat.get('paths', [])
        if path in cat['paths']:
            return True
        cat['paths'].append(path)
        self.categories_list.update(q, {'$set': {'paths': cat['paths']}})
        'New path for {} has been add'.format(title)
        return False

    def save_pages(self, page_ids):
        pages_url = page_content_url.format('|'.join(page_ids))
        pages_data = self.get_json(pages_url)
        pages = pages_data['query']['pages']
        for page_id, page in pages.iteritems():
            text = page.pop('revisions')[0]['*']
            page['title'] = page['title'].encode('utf8')
            page['url'] = page_url.format(page['title'])
            page['text'] = text
            self.write(page)
            self.done_dbelement(page['pageid'])
        print('{} pages have been downloaded'.format(len(page_ids)))

    def download_category(self, pageid=None, title=None, path='', db_item=None, n=1):
        if n > self.N:
            return
        self.add_path(path, title)
        if db_item and db_item.get('done') or self.check_is_done(pageid, title):
            return
        print('=================')
        print('Start getting pages for "{}"'.format(title))
        print(n)
        print(path)
        url = subcat_and_pages_url.format(title)
        data = self.get_json(url)
        try:
            children = data['query']['categorymembers']
        except Exception as e:
            print(url)
            print(data)
            raise(e)
        if len(children) == 0:
            self.done_dbelement(pageid=pageid, title=title)
            print('Empty category {}'.format(title))
            print('--->Nothing to download in category "{}"'.format(title))
            return
        # self.db_items.items.insert_many(children)
        page_ids = []
        subcats = []
        parents = path.split('/')
        for ch in children:
            db_item = self.db_items.get_or_create(ch, {'pageid': ch['pageid']})
            if 'Category:' in ch['title']:
                if parents.count(ch['title']) == 0:
                    subcats.append((ch, db_item))
                else:
                    print('( CYCLE IN PATH )')
            elif not db_item.get('done'):
                page_ids.append(str(ch['pageid']))
        if len(page_ids) != 0:
            self.save_pages(page_ids)
            print('Save all pages for "{}"'.format(title))
        else:
            print('--->No new pages in category "{}"'.format(title))

        print('Category "{}" has {} subcategories'.format(title, len(subcats)))
        for cat, db_item in subcats:
            self.download_category(cat['pageid'], cat['title'].encode('utf8'),
                                   path + '/' + title, db_item, n + 1)

        self.done_dbelement(pageid=pageid, title=title)
        print('Category {} is done'.format(title))

    def run(self):
        for title in root_categories:
            self.download_category(title=title.encode('utf8'), path=title)


def download(lama):
    lich = WikiLich(lama)
    lich.run()
