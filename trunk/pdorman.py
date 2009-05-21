'''Converts Dilbert.txt from pdorman@umich.edu into a bulk-uploadable format'''
import re
from pprint import pprint

start = True
comics = []
comic = {}
for line in open('D:/temp/Dilbert.txt'):
    if line == '\n':
        comics.append(comic)
        comic = {}
        start = True
        continue
    else: start = False

    titlematch = re.match(r'<?dilbert?(\d\d)(\d\d)(\d\d)', line)
    quotematch = re.match(r'<([^>]*)>(.*)', line)
    if titlematch: comic['date'] = '20' + titlematch.group(3) + titlematch.group(1) + titlematch.group(2)
    if quotematch:
        comic['desc'] = comic.get('desc', '') + quotematch.group(1).capitalize() + ': ' + quotematch.group(2).capitalize() + '\\n'

for comic in comics:
    print comic['date'] + '\t' + comic['desc']
