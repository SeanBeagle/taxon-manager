import requests
import argparse
import sqlite3
import csv
import os
from time import sleep

"""
AUTHOR: Sean Beagle
 EMAIL: SeanBeagle@gmail.com
 ABOUT: Download GenBank files for SARS-CoV-2 Research
"""

class Eutils:
    URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    
    @staticmethod
    def search(db, or):
        fcgi = 'esearch.fcgi'
        params = '?' + '&'.(f"{k}={v}" for k,v in kwargs.items())
        r = requests.get(URL + fcgi + params)

    @staticmethod
    def fetch(id, rettype, out_dir, **kwargs):
        fcgi = 'efetch.fcgi'
        params = "?" + '&'.(f"{k}={v}" for k,v in kwargs.items()) 
        r = requests.get(URL + fcgi + params)
        if r.ok:
            file_out = id + '.SARS-CoV-2' 
            with open(file_out, 'w') as fh:
                fh.write(r.text)
            print(f"Wrote file: {file_out}")
        else:
            print(f"...ERROR! Could not download '{id}'")
EUTILS = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
FETCH  = 'efetch.fcgi'

def get_genbank(accession):
    params = '?db=nuccore&rettype=gb&id=' + accession
    r = requests.get(EUTILS + FETCH + params)
    if r.ok:
        file_out = accession + '.SARS-CoV-2.gb'
        with open(file_out, 'w') as fh:
            fh.write(r.text)
        print(f"SUCCESS! {file_out}")
    else:
        print(f"  ERROR! Could not download '{accession}'")

def get_many_genbank(csv_in):
    rows = csv.DictReader(open(csv_in))
    for row in rows:
        accession = row.get('Accession') or row.get('accession')
        if accession:
            get_genbank(accession)
        sleep(0.34)

get_fna(accession):
    params  = '?db=nuccore&rettype=gb&id=' + accession
    r = requests.get(EUTILS + FETCH + params)
    if r.ok:
        file_out = accession + '.SARS-CoV-2' + '.fa'
        with open(file_out, 'w') as fh:
            fh.write(r.text)
        print(f"SUCCESS! {file_out}")
    else:
        print("  ERROR! Could not download '{accession}'")
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument('--id')
    options.add_argument('--csv')
    args = parser.parse_args()
    if args.id:
        get_genbank(args.id)
    elif args.csv:
        get_many_genbank(args.csv)
# result = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=MT123292&rettype=gb')
