# -*- coding: utf-8 -*-
from lama.lich import Lich







class Form(Item):
    def __init__(self, item):
        self.item = item
        self.download()
        self.downloaded = False

    def download(self):
        url = '{}/{}'.format(settings.BASE_URL, self.item['file_name'])
        name = get_name(url)

        in_db = self.check(name)
        if in_db:
            return

        path = get_path(self.item['form_type'], name)
        self.item['name'] = name
        self.item['url'] = url
        self.item['path'] = path
        time.sleep(settings.SLEEP)
        super(Form, self).download(url, path)
        self.downloaded = True
        self.write(self.item)


class Index(Item):
    def __init__(self, year, qtr, n=0, path=None):
        self.n = n
        url = url = '{}/edgar/full-index/{}/QTR{}/company.idx'.format(settings.BASE_URL, year, qtr)
        name = get_name(url)
        if path is None:
            self.download(url, name)
        else:
            self.proccess(path, name, url)

    def get_date(self, body):
        last_date_str = re.findall('Last Data Received:\s+\w+ \d+, \d+', body)
        if len(last_date_str) == 0:
            return
        last_date = last_date_str[0].replace('Last Data Received:', '').strip()
        return datetime.datetime.strptime(last_date, '%B %d, %Y')

    def _clean_line_data(self, line):
        if len(line) == 4:
            line = [''] + line
        STOPPERS = ['/TA', 'NA', '/FI', '/ADV', 'LLC', 'TECHNOLOGIES CORP', 'CORP', 'LEO']
        for ptrn in STOPPERS:
            if ptrn in line:
                line[0] += ptrn
                line.remove(ptrn)
        return line

    def process_line(self, line, start):
        line = [el.strip() for el in line.replace('\n', '').split('  ') if el.strip().replace('-', '')]
        if len(line) == 0:
            return start
        if line == settings.IDX_HEADER:
            return True
        if not start:
            return
        line = self._clean_line_data(line)
        data = dict(zip(settings.IDX_HEADER, line))
        if data['Form Type'] not in settings.ALLOWED_FORMS:
            return True
        print data
        company_forms = dict(
            form_type=data['Form Type'],
            date=datetime.datetime.strptime(data['Date Filed'], '%Y-%m-%d'),

            company_name=data['Company Name'],
            cik=data['CIK'],
            file_name=data['File Name'],
        )
        form = Form(company_forms)
        self.n += 1
        print '{} form have been downloaded'.format(self.n)
        return form

    def proccess(self, path, name, url):
        in_db = self.check(name)
        item = in_db or dict(
            form_type='index',
            name=name,
            path=path,
            url=url,
        )
        with open(path) as idx:
            start = None
            for line in idx.readlines():
                if item.get('date') is None:
                    item['date'] = self.get_date(line)
                start = self.process_line(line, start)
        if in_db is None:
            self.write(item)

    def download(self, url, name):
        path = get_path('index', name)
        super(Index, self).download(url, path)
        self.proccess(path, name, url)


START_YEAR = 1993
END_YEAR = 2016


def download_indexes():
    for year in reversed(xrange(START_YEAR, END_YEAR + 1)):
        for qtr in xrange(1, 5):
            print 'Download index year {} qtr {}'.format(year, qtr)
            idx = Index(year, qtr)

if __name__ == "__main__":
    # download_indexes
    # n = 0
    # for year in reversed(xrange(START_YEAR, END_YEAR + 1)):
    #     for qtr in xrange(1, 5):
    #         idx = Index(year, qtr, n)
    #         n = idx.n
    # Index(
    #     2016, 1, path='/Users/kunla/lamedoc/alpaka/TMP/index/262ad775edcd3322374e63c63053d1465c13dd9331187059d927091b')

