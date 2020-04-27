# AUTHOR: Sean Beagle
#  EMAIL: SeanBeagle@gmail.com
#    URL: SeanBeagle.com
#         StrongLab.org

# STANDARD LIBRARY
import sqlite3
from datetime import datetime
# EXTERNAL PACKAGES
from Bio import GenBank
# PROJECT FILES
from .config import Config

def format_genbank_date(date):
    month = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 
              'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08', 
              'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12']
    try:
        d, m, y = date.split('-')
        return f"{y}-{month[m]}-{d.zfill(2)}"
    except:
        return None


def now():
    """Store datetime.now() as iso formatted string"""
    return datetime.now().strftime('%Y-%m-%d, %H:%M:%S"')


def init_database():
    con = sqlite3.connect('project.db')
    cur = conn.cursor()

    # CREATE TABLES
    cur.executescript("""
        CREATE TABLE Project (
           organism     TEXT,
           date_created TEXT,
           created_by   TEXT,
           basedir      TEXT,
           taxon        TEXT
        );
        CREATE TABLE Isolate (
            accession      TEXT PRIMARY KEY,
            organism       TEXT,
            date_released  TEXT, 
            date_collected TEXT,
            country        TEXT,
            host           TEXT
        );
        CREATE TABLE GenBank (
            accession       TEXT PRIMARY KEY,
            filepath        TEXT UNIQUE NOT NULL,
            version         TEXT,
            date_downloaded TEXT,
            downloaded_by   TEXT,
            num_features    REAL,
            basepairs       REAL
        );
        CREATE TABLE Feature (
            id        INTEGER PRIMARY KEY,
            accession TEXT,
            key       TEXT,
            start     REAL,
            stop      REAL
        );
    """)

    con.commit()
    con.close()

def isolate_from_gb(filepath):
    print("Adding GenBank to Database")
    gb = GenBank.read(open(filepath)
    source = genbank_source_data(gb)
    columns  = ['accession', 'date_released', 'date_collected' 'country', 'host']
    data = {
        'accession': gb.accession,
        'date_released': format_genbank_date(gb.date),
        'date_collected': source.get('collection_date'),
        'country': source.get('country'),
        'host': source.get('host')
    }


def add_genbank_feature(accession):
    print("[INFO] Adding GenBank Feature")


def genbank_source_data(gb):
    source = gb.features[0]
    if source.key != 'source':
        return None
    data = {}
    for q in source.qualifiers:
        k, v = q.key.strip('=/'), q.value.strip('"')
        data[k] = v
            

