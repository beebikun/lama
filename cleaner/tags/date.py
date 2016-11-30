import re


MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


def generate_month_range():
    months = []
    for m in MONTHS:
        l = len(m) - 3
        if l == 0:
            months.append(m)
        else:
            months.append('%s[a-z]{0,%s}' % (m[:3], str(l)))
    return '|'.join(months)

day_range = '(?:' + '|'.join(['{}|{}'.format('0' + str(i), str(i)) if i < 10 else str(i)
                              for i in range(1, 31)]) + ')'
month_name_range = '(?:' + generate_month_range() + ')'
month_range_one = '(?:' + '|'.join([str(i) for i in range(1, 13)]) + ')'
month_range_two = '(?:' + '|'.join([('0' if i < 10 else '') + str(i) for i in range(1, 13)]) + ')'
month_range = '(?:' + month_range_one + '|' + month_range_two + ')'
year_range = '(?:' + '\d{4}|\d{2}' + ')'
date_formats = [
    '%(days)s\s*(?:/\|\-|_)\s*%(months)s(?:/\|\-|_)s*%(years)s' % dict(
        days=day_range, months=month_range, years=year_range),
    '\d{4}\s*-\s*%(months)s\s*-\s*%(days)s' % dict(days=day_range, months=month_range),
]
month_two_dec = [
    '%(days)s\s*\.\s*%(months)s\s*\.\s*%(years)s' % dict(days=day_range, months=month_range_two, years=year_range),
]

month_named_formats = [
    '%(months)s\s+%(days)s,\s*%(years)s' % dict(days=day_range, months=month_name_range, years=year_range),
    '%(months)s\s*(?:/\|\-|_\.)\s*%(days)s\s*(?:/\|\-|_)\s*%(years)s' % dict(days=day_range, months=month_name_range, years=year_range),
    '%(months)s\s+\d{4}' % dict(days=day_range, months=month_name_range, years=year_range),
    '%(days)s\s*\-\s*%(months)s\s*\-\s*%(years)s' % dict(days=day_range, months=month_name_range, years=year_range),
    '%(days)s\s+%(months)s\s+%(years)s' % dict(days=day_range, months=month_name_range, years=year_range),
]


class DateCompile(object):
    pattern = 'date'

    def subn(self, tag, text):
        text, n1 = re.subn('Q\d\s*\d{4}', tag, text, flags=re.I)
        text, n2 = re.subn('|'.join(month_named_formats), tag, text, flags=re.I)
        text, n3 = re.subn('|'.join(month_named_formats), tag, text, flags=re.I)
        text, n4 = re.subn('|'.join(month_two_dec), tag, text, flags=re.I)
        text, n5 = re.subn('|'.join(date_formats), tag, text, flags=re.I)
        return text, 0

    # def subn(self, tag, text):
    #     return self.sub(tag, text)


date_compile = DateCompile()
