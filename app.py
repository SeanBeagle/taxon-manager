# STANDARD LIBRARY
from datetime import datetime
from io import StringIO
from time import sleep
import os
import getpass
import logging              # TODO(seanbeagle): Configure logging and convert print statements
# EXTERNAL PACKAGES
import Bio.GenBank
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# PROJECT FILES
import config
import eutils

# initialize application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class BaseModel(db.Model):
    __abstract__ = True

    @classmethod
    def insert(cls, **kwargs):
        record = cls(**kwargs)
        print(f"Adding Record {record}")
        db.session.add(record)
        db.session.commit()
        return record


class Project(BaseModel):
    """A Project is defined by its organism"""

    __tablename__ = 'Project'

    id = db.Column(db.Integer, primary_key=True)
    organism = db.Column(db.String, unique=True, nullable=False)
    alias = db.Column(db.String, nullable=False)
    date_created = db.Column(db.String)
    created_by = db.Column(db.String)
    basedir = db.Column(db.String)

    def __repr__(self):
        return f"<Project(id={self.id}, organism='{self.organism}')>"


class Isolate(BaseModel):
    """An Isolate is defined by its NCBI accession"""

    __tablename__ = 'Isolate'

    accession = db.Column(db.String, primary_key=True)
    uid = db.Column(db.String, unique=True)
    organism = db.Column(db.String, nullable=False)
    date_released = db.Column(db.String)
    date_collected = db.Column(db.String)
    country = db.Column(db.String)
    host = db.Column(db.String)

    def __repr__(self):
        return f"<Isolate(accession='{self.accession}', organism='{self.organism}')>"

    @classmethod
    def from_genbank(cls, filepath: str):
        gb = Bio.GenBank.read(open(filepath))
        source = GenBank.get_source_data(gb)

        record = cls.insert(
            accession=gb.accession,
            date_released=GenBank.format_date(gb.date),
            host=source.get('host'),
            date_collected=source.get('collection_date'),
            country=source.get('country'),
        )
        return record


class GenBank(BaseModel):
    """GenBank Files"""

    __tablename__ = 'GenBank'

    id = db.Column(db.Integer, primary_key=True)
    accession = db.Column(db.String, nullable=False)
    version = db.Column(db.String, nullable=False, unique=True)
    filepath = db.Column(db.String)
    date_downloaded = db.Column(db.String)
    downloaded_by = db.Column(db.String)
    num_features = db.Column(db.Integer)

    def __repr__(self):
        return f"<GenBank(id={self.id}, version='{self.version}, num_features={self.num_features}')>"

    @staticmethod
    def read_string(string: str):
        try:
            return Bio.GenBank.read(StringIO(string))
        except ValueError:
            print("[WARN] No Records Found in GenBank string")

    @staticmethod
    def get_source_data(gb: Bio.GenBank):
        try:
            assert gb.features[0].key == 'source', 'source information not found'
            source = gb.features[0]
            if source.key != 'source':
                return None
            data = {}
            for q in source.qualifiers:
                key = q.key.strip('=/')
                value = q.value.strip('"')
                data[key] = value
            return data
        except AssertionError as e:
            print(f"[WARN] {e}")

    @classmethod
    def add_file(cls, filepath: str):
        try:
            print("Trying to add genbank file to database...")
            gb = Bio.GenBank.read(open(filepath))
            record = cls.insert(
                accession=gb.accession,
                version=gb.version,
                filepath=filepath,                  # TODO: is this abspath?
                date_downloaded=now(),
                downloaded_by=getpass.getuser(),
                num_features=len(gb.features))
            return record
        except Exception as e:
            print("Error inserting GenBank record" + e)

    @staticmethod
    def fetch(id: str):
        print(f"[INFO] Fetching GenBank id: {id}")

        r = eutils.fetch(db='nuccore', id=id, rettype='gb')
        if r.ok:
            gb = GenBank.read_string(r.text)
            filename = f"{gb.accession}{'.' + config.taxon if config.taxon else ''}.gb"
            file_out = os.path.join(FileSystem.dir['genbank'], filename)
            record = GenBank.query.filter_by(version=gb.version).first()

            if record and os.path.exists(record.filepath):
                print(f"[WARN] {file_out} already exists")
            else:
                with open(file_out, 'w') as fh:
                    fh.write(r.text)
                GenBank.add_file(filename)
                print(f"[INFO] Fetched file: {file_out}")
            return filename
        else:
            print(f"[WARN] Could not download '{id}'")

    @staticmethod
    def format_date(date: str):
        month = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
                 'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
        try:
            d, m, y = date.split('-')
            return f"{y}-{month[m]}-{d.zfill(2)}"
        except Exception as e:
            print(e)
            return None


class Feature(BaseModel):
    """Features of a GenBank file"""

    __tablename__ = 'Feature'

    id = db.Column(db.Integer, primary_key=True)
    genbank_id = db.Column(db.Integer, db.ForeignKey('GenBank.id'))
    type = db.Column(db.String, nullable=False)
    start = db.Column(db.Integer)
    stop = db.Column(db.Integer)
    genbank = db.relationship('GenBank', backref=db.backref('features', lazy=True))

    def __repr__(self):
        return f"<Feature(id={self.id}, type={self.type}, genbank={self.genbank.version})>"

    def __len__(self):
        return self.stop - self.start


class FileSystem:
    dir = {}

    @classmethod
    def build(cls, basedir):
        cls.add_directory('basedir', basedir)
        cls.add_directory('genbank', os.path.join(basedir, 'genbank'))

    @classmethod
    def use(cls, basedir):
        cls.use_directory('basedir', basedir)
        cls.use_directory('genbank', os.path.join(basedir, 'genbank'))

    @classmethod
    def use_directory(cls, key, directory):
        if os.path.isdir(directory):
            cls.dir[key] = directory
        else:
            print(f"[WARN] {directory} does not exist!")

    @classmethod
    def add_directory(cls, key, directory):
        """Add directory to dictionary. Make directory if does not exist"""
        try:
            os.makedirs(directory)
            print(f"[INFO] Created directory {directory}")
            cls.dir[key] = directory
        except FileExistsError:
            print(f"[INFO] Directory {directory} already exists")
            cls.dir[key] = directory
        except PermissionError:
            print(f"[WARN] Do not have permission to make {directory}")


def sync_ncbi():
    print("[INFO] Syncing to NCBI")
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
            gb = GenBank.fetch(id)
            Isolate.from_genbank(gb)

            sleep(1/3)  # LIMIT 3 REQUESTS PER SECOND
    else:
        print(f"[WARN] Error with request: {r.url}")


def now():
    """Store datetime.now() as iso formatted string"""
    return datetime.now().strftime('%Y-%m-%d, %H:%M:%S"')


def init():
    FileSystem.build(config.basedir)
    db.create_all()


def update():
    print("update not created")
    FileSystem.use(config.basedir)
    sync_ncbi()
