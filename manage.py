"""
AUTHOR: Sean Beagle
 EMAIL: SeanBeagle@gmail.com
 ABOUT: Download GenBank files for SARS-CoV-2 Research
"""
# PYTHON STANDARD LIBRARY
import argparse
import sqlite3
import csv
import os
from io import StringIO
from time import sleep
# EXTERNAL LIBRARIES
from Bio import GenBank
import requests
# PROJECT FILES
from config import Config
#from .entrez import Eutils

class Eutils:
    """Entrez Eutils API wrapper for downloading NCBI files
    TODO(seanbeagle): Make this a separate module with CLI tools
    """
    URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    
    @classmethod
    def search(cls, db, organism, retmax=0):
        fcgi = 'esearch.fcgi'
        params = f"?db={db}&term=complete+genome+AND+{organism}[organism]&retmax={retmax}&retmode=json"
        url = f"{cls.URL}{fcgi}{params}"
        return requests.get(url)

    @classmethod
    def fetch(cls, db, id, rettype):
        fcgi = 'efetch.fcgi'
        params = f"?db={db}&id={id}&rettype={rettype}"
        url = f"{cls.URL}{fcgi}{params}"
        return requests.get(url)


def update_genbank(organism):
    # DETERMINE NUMBER OF RECORDS MATCHING TAXON   
    count = 0
    r = Eutils.search('nuccore', organism)
    if r.ok:
        count = r.json()['esearchresult']['count']
        print(f"[INFO] Found {count} organisms that match {organism}")
    else:
        print(f"[WARN] Error with request: {r.url}")
    # IDENTIFY ALL RECORD ID'S AND BEGIN DOWNLOADING GENBANK FILES
    r = Eutils.search('nuccore', organism, retmax=count)
    num_pass = 0
    num_fail = 0
    if r.ok:
        for id in r.json()['esearchresult']['idlist']:
            fetch_gb(id, Config.TAXON)
            sleep(1/3)  # LIMIT 3 REQUESTS PER SECOND
    else:
        print(f"[WARN] Error with request: {r.url}")


def fetch_gb(id, taxon=None):
    r = Eutils.fetch(db='nuccore', id=id, rettype='gb')
    if r.ok:
        gb = GenBank.read(StringIO(r.text))
        filename = f"{gb.locus}{'.' + taxon if taxon else ''}.gb"
        file_out = os.path.join(Config.GENBANK_DIR, filename)
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
    update_genbank(Config.ORGANISM)


def init_directory_tree(base_dir):
    print("[INFO] Initializing Directory Tree")


def init_database():
    print("[INFO] Initializing Database")


def init():
    print("[INFO] Initializing project")
    init_directory_tree(Config.BASE_DIR)
    init_database()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument('--init', action='store_true')
    options.add_argument('--update', action='store_true')
    options.add_argument('--id')
    options.add_argument('--csv')
    options.add_argument('--organism', nargs='+')
    args = parser.parse_args()
    if args.init:
        init()
    elif args.update:
        update()

    elif args.id:
        fetch_gb(id=args.id, taxon=TAXON)
    elif args.csv:
        fetch_csv(args.csv)
    elif args.organism:
        search_organism(db='nuccore', organism='+'.join(args.organism))
# result = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=MT123292&rettype=gb')
