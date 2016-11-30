import hashlib
import subprocess
import urllib
import json

# path = 'https://en.wikipedia.org/w/api.php?' + \
#        'format=json&action=query&generator=categorymembers&' + \
#        'gcmtitle={}&prop=categories&cllimit=max&gcmlimit=max'

# wget(path.format('Category:Economy'))
#  dont download pages List_of
# https://en.wikipedia.org/wiki/Category:Algorithmic_trading
# https://en.wikipedia.org/wiki/Category:Behavioral_finance
# https://en.wikipedia.org/wiki/Category:Derivatives_(finance)
# https://en.wikipedia.org/wiki/Category:Financial_economics
# https://en.wikipedia.org/wiki/Category:Financial_markets
# https://en.wikipedia.org/wiki/Category:Financial_regulation
# https://en.wikipedia.org/wiki/Category:Financial_regulation_in_the_United_States
# https://en.wikipedia.org/wiki/Category:Finance_theories
# https://en.wikipedia.org/wiki/Category:Fixed_income_market
# https://en.wikipedia.org/wiki/Category:Market_data
# https://en.wikipedia.org/wiki/Category:Money_market_instruments
# https://en.wikipedia.org/wiki/Category:Private_equity
# https://en.wikipedia.org/wiki/Category:Prediction_markets
# https://en.wikipedia.org/wiki/Category:Securities_(finance)
# https://en.wikipedia.org/wiki/Category:Systemic_risk


import time


class Lich(object):
    subfolder = ''

    def __init__(self, lama):
        self.lama = lama
        self.STORAGE = lama.create_storage('DATA')

    def get_name(self, url):
        return hashlib.sha224(url).hexdigest()

    def wget(self, url, path):
        subprocess.call(['wget', url, '-O', path])

    def get_json(self, url):
        response = urllib.urlopen(url)
        try:
            data = json.loads(response.read())
            time.sleep(.5)
        except Exception, e:
            print url
            print response.read()
            raise e
        return data

    def write(self, item):
        item['name'] = self.get_name(item['url'])
        text = item.pop('text')
        item['file_path'] = self.STORAGE.write(text, item['name'], self.subfolder)
        self.lama.db_items.get_or_create(item)

    def run(self):
        pass
