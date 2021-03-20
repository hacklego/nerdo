from datetime import datetime, timedelta
from base64 import b64encode
from requests import get
from typing import Any, Iterator, Optional

import zipfile
import numpy as np
import argparse
import sys

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

    return matrix[size_x-1, size_y-1]


def parse_nerd(
        keywords: str
) -> (list, list):

    high_confidence_domains = list()
    low_confidence_domains= list()

    filename = "domain-names.txt"

    with open(filename, 'r') as f:
        for line in f:
            domain_name = line.split('\n')[0].split('.')[0]

            for keyword in keywords:
                if levenshtein(keyword, domain_name) <= 1:
                    high_confidence_domains.append(line.split('\n')[0])
                elif keyword in domain_name:
                    low_confidence_domains.append(line.split('\n')[0])

    return high_confidence_domains, low_confidence_domains


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "keywords",
        help="string or file with lines to process. "
        "If none then stdin will be use",
        nargs="*",
    )
    args = parser.parse_args()

    keywords = list(read_text_targets(args.keywords))

    download_yesterday_domains_from_whoisdownload()
    h, l = parse_nerd(keywords)

    for result in h:
        print("high {}".format(result))

    for result in l:
        print("low {}".format(result))


def read_text_targets(targets: Any) -> Iterator[str]:
    yield from read_text_lines(read_targets(targets))


def read_targets(targets: Optional[Any]) -> Iterator[str]:
    """Function to process the program ouput that allows to read an array
    of strings or lines of a file in a standard way. In case nothing is
    provided, input will be taken from stdin.
    """
    if not targets:
        yield from sys.stdin

    for target in targets:
        try:
            with open(target) as fi:
                yield from fi
        except FileNotFoundError:
            yield target


def read_text_lines(fd: Iterator[str]) -> Iterator[str]:
    """To read lines from a file and skip empty lines or those commented
    (starting by #)
    """
    for line in fd:
        line = line.strip()
        if line == "":
            continue
        if line.startswith("#"):
            continue

        yield line

if __name__ == '__main__':
    main()

