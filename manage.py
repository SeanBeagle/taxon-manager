# PYTHON STANDARD LIBRARY
import argparse
import os
from io import StringIO
from time import sleep
# EXTERNAL LIBRARIES
from Bio import GenBank
# PROJECT FILES
import config
import app
import eutils


def update_genbank():
    # DETERMINE NUMBER OF RECORDS MATCHING organism
    count = 0
    r = eutils.search('nuccore', config.organism)
    if r.ok:
        count = r.json()['esearchresult']['count']
        print(f"[INFO] Found {count} organisms that match {config.organism}")
    else:
        print(f"[WARN] Error with request: {r.url}")
    # IDENTIFY ALL RECORD ID'S AND BEGIN DOWNLOADING GENBANK FILES
    r = eutils.search('nuccore', config.organism, retmax=count)
    num_pass = 0
    num_fail = 0
    if r.ok:
        for id in r.json()['esearchresult']['idlist']:
            fetch_gb(id, config.taxon)
            sleep(1/3)  # LIMIT 3 REQUESTS PER SECOND
    else:
        print(f"[WARN] Error with request: {r.url}")


def fetch_gb(id, taxon=None):
    r = eutils.fetch(db='nuccore', id=id, rettype='gb')
    if r.ok:
        gb = GenBank.read(StringIO(r.text))
        filename = f"{gb.locus}{'.' + taxon if taxon else ''}.gb"
        file_out = os.path.join(config.genbank_dir, filename)
        if os.path.exists(file_out): 
            print(f"[WARN] {file_out} already exists")
        else:
            with open(file_out, 'w') as fh:
                fh.write(r.text)
            print(f"[INFO] Fetched file: {file_out}")
    else:
        print(f"[WARN] Could not download '{id}'")


def update():
    print("[INFO] Updating files from NCBI")
    update_genbank()


def init():
    print("[INFO] Initializing project")
    app.init()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['init', 'update'])
    # options = parser.add_mutually_exclusive_group(required=True)
    # options.add_argument('--init', action='store_true')
    # options.add_argument('--update', action='store_true')
    args = parser.parse_args()
    if args.action == 'init':
        init()
    elif args.action == 'update':
        update()

