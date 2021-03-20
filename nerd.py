from datetime import datetime, timedelta
from base64 import b64encode
from requests import get

import zipfile
import numpy as np

KEYWORDS = 'one-esecurity', 'oneesecurity', 'onesecurity'


def download_yesterday_domains_from_whoisdownload():

    BASE_URI = "https://www.whoisdownload.com/download-panel/free-download-file/"
    yesterday = datetime.now() - timedelta(days=1)
    filename = yesterday.strftime("%Y-%m-%d")+'.zip'
    b64_filename = b64encode(filename.encode('ascii'))

    resource = b64_filename.decode() + '/nrd/home'

    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }


    r = get(BASE_URI+resource, headers=headers)

    with open(filename, 'wb') as f:
        f.write(r.content)

    with zipfile.ZipFile(filename, 'r') as zip_file:
        zip_file.extractall('.')


def levenshtein(
        seq1: str,
        seq2: str
) -> int:

    size_x = len(seq1) + 1
    size_y = len(seq2) + 1

    matrix = np.zeros((size_x, size_y))

    for x in range(size_x):
        matrix[x, 0] = x

    for y in range(size_y):
        matrix[0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            minimum = min(matrix[x-1, y], matrix[x-1, y-1], matrix[x, y-1])
            if seq1[x-1] == seq2[y-1]:
                matrix[x, y] = minimum
            else:
                matrix[x, y] = minimum + 1

    #print(matrix)

    return matrix[size_x-1, size_y-1]


def parse_nerd(
) -> (list, list):

    high_confidence_domains = list()
    low_confidence_domains= list()

    filename = "domain-names.txt"

    with open(filename, 'r') as f:
        for line in f:
            domain_name = line.split('\n')[0].split('.')[0]

            for keyword in KEYWORDS:
                if levenshtein(keyword, domain_name) <= 1:
                    high_confidence_domains.append(line.split('\n')[0])
                elif keyword in domain_name:
                    low_confidence_domains.append(line.split('\n')[0])

    return high_confidence_domains, low_confidence_domains



if __name__ == '__main__':
    download_yesterday_domains_from_whoisdownload()
    h, l = parse_nerd()

    print('There are {} high confidence domains and {} low confidence domains:\n'.format(len(h), len(l)))

    print('High\n')
    for domain in h:
        print(domain)

    print('\nLow\n')
    for domain in l:
        print(domain)
