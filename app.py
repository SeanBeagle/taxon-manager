# STANDARD LIBRARY
from datetime import datetime
from io import StringIO
# EXTERNAL PACKAGES
import Bio.GenBank
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# PROJECT FILES
import config


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.database
db = SQLAlchemy(app)


class Project(db.Model):
    __tablename__ = 'Project'

    id = db.Column(db.Integer, primary_key=True)
    organism = db.Column(db.String, nullable=False)
    taxon = db.Column(db.String)
    date_created = db.Column(db.String)
    created_by = db.Column(db.String)
    basedir = db.Column(db.String)

    def __repr__(self):
        return f"<Project(id={self.id}, organism='{self.organism}')>"


class Isolate(db.Model):
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
        record = cls(
            accession=gb.accession,
            date_released=format_genbank_date(gb.date),
            date_collected=source.get('collection_date'),
            country=source.get('country'),
            host=source.get('host')
        )
        db.session.add(record)
        db.session.commit()
        return record


class GenBank(db.Model):
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
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def get_source_data(gb: Bio.GenBank):
        source = gb.features[0]
        if source.key != 'source':
            return None
        data = {}
        for q in source.qualifiers:
            key = q.key.strip('=/')
            value = q.value.strip('"')
            data[key] = value
        return data


class Feature(db.Model):
    __tablename__ = 'Feature'

    id = db.Column(db.Integer, primary_key=True)
    genbank_id = db.Column(db.Integer)
    type = db.Column(db.String, nullable=False)
    start = db.Column(db.Integer)
    stop = db.Column(db.Integer)
    genbank = db.relationship('GenBank', backref=db.backref('features', lazy=True))

    def __repr__(self):
        return f"<Feature(id={self.id}, type={self.type}, genbank={self.genbank.version})>"

    def __len__(self):
        return self.stop - self.start


def format_genbank_date(date: str):
    month = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 
             'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
             'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
    try:
        d, m, y = date.split('-')
        return f"{y}-{month[m]}-{d.zfill(2)}"
    except Exception as e:
        print(e)
        return None


def now():
    """Store datetime.now() as iso formatted string"""
    return datetime.now().strftime('%Y-%m-%d, %H:%M:%S"')


def build_database():
    print("Initializing Database")
    db.create_all()


def build_filesystem():
    print("Initializing Directory Tree")







            

