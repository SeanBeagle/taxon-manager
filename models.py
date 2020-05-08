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
logging.basicConfig(filename=f'{os.path.join(config.basedir, config.taxon)}.log', level=logging.DEBUG)


class BaseModel(db.Model):
    __abstract__ = True

    @classmethod
    def insert(cls, **kwargs):
        try:
            record = cls(**kwargs)
            db.session.add(record)
            db.session.commit()
            logging.info(f"Inserted {record} into {cls.__name__}")
            return record
        except Exception as e:
            logging.warning(f"Error inserting record into {cls.__name__}: {e}")


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
        return self.organism


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
        return self.accession

    @classmethod
    def from_genbank(cls, filepath: str):
        try:
            gb = GenBank.read(file=filepath)
            source = GenBank.get_source_data(gb)
            return cls.insert(
                accession=gb.accession[0],
                organism=gb.organism,
                date_released=GenBank.format_date(gb.date),
                host=source.get('host'),
                date_collected=source.get('collection_date'),
                country=source.get('country'),
            )
        except Exception as e:
            logging.warning(f"Error inserting {filepath} to {cls.__name__}: {e}")


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
    length = db.Column(db.Integer)

    def __repr__(self):
        return self.filepath

    @classmethod
    def read(cls, **kwargs):
        """Return Bio.GenBank object from string or file
        TODO(seanbeagle): Return dictionary of genbank data instead of Bio.GenBank object
        """
        if kwargs.get('file'):
            try:
                return Bio.GenBank.read(open(kwargs.get('file')))
            except Exception as e:
                logging.warning(f"Problem reading: {e}")
        elif kwargs.get('string'):
            try:
                return Bio.GenBank.read(StringIO(kwargs.get('string')))
            except Exception as e:
                logging.warning(f"Problem reading: {e}")
        else:
            logging.debug(f"{cls.__name__}.read() requires keyword argument: file or string")

    @staticmethod
    def get_source_data(gb: Bio.GenBank):
        """Return source data from Bio.GenBank object
        TODO(seanbeagle): Move this functionality to the read() method
        """
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
            logging.warning(f"{e}")

    @staticmethod
    def to_dict(gb: Bio.GenBank):
        # TODO(seanbeagle): Return fields from Bio.GenBank object as dictionary
        logging.debug("to_dict() method currently has no function")

    @classmethod
    def add_file(cls, filepath: str):
        """TODO(seanbeagle): Create scraping tool for genbank data similar to get_source_data()"""
        try:
            gb = GenBank.read(file=filepath)
            accession = gb.accession[0]
            logging.debug(f"Adding {accession} to {cls}...")
            record = cls.insert(
                accession=accession,
                version=gb.version,
                filepath=filepath,                  # TODO: Ensure this is absolute filepath
                date_downloaded=now(),
                downloaded_by=getpass.getuser(),
                num_features=len(gb.features),
                length=len(gb))
            return record
        except Exception as e:
            logging.debug(f"Could not insert GenBank record: {e}")

    @staticmethod
    def fetch(id: str):
        logging.info(f"Fetching GenBank id={id}")

        r = eutils.fetch(db='nuccore', id=id, rettype='gb')
        if r.ok:
            gb = GenBank.read(string=r.text)
            accession = gb.accession[0]
            filename = f"{accession}{'.' + config.taxon if config.taxon else ''}.gb"
            file_out = os.path.join(FileSystem.dir['genbank'], filename)
            record = GenBank.query.filter_by(version=gb.version).first()

            if record and os.path.exists(record.filepath):
                logging.info(f"{accession} already exists as file='{record.filepath}' and GenBank.id={record.id}")
            else:
                with open(file_out, 'w') as fh:
                    fh.write(r.text)
                GenBank.add_file(file_out)
                print(f"[INFO] Fetched file: {file_out}")
            return file_out
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
        logging.info(f"{count} organisms match {config.organism}")
    else:
        logging.warning(f"Error with HTTP request: {r.url}")
    # IDENTIFY ALL RECORD ID'S AND BEGIN DOWNLOADING GENBANK FILES
    r = eutils.search('nuccore', config.organism, retmax=count)
    if r.ok:
        for id in r.json()['esearchresult']['idlist']:
            gb = GenBank.fetch(id)
            Isolate.from_genbank(gb)
            sleep(1/3)  # LIMIT 3 REQUESTS PER SECOND
    else:
        logging.warning(f"ERROR: {r.status_code} for {r.request.method} Request: {r.url}")


def now():
    """Store datetime.now() as iso formatted string"""
    return datetime.now().strftime('%Y-%m-%d, %H:%M:%S')


def init():
    FileSystem.build(config.basedir)
    db.create_all()


def update():
    FileSystem.use(config.basedir)
    sync_ncbi()
