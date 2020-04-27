import os

class Config:
    """ class based configuration for project 
    options:
        BASEDIR: Root directory of project
        GENBANK_DIR: Directory
        ORGANISM: Name of organism in NCBI
    """
    BASEDIR = '/Strong/proj/.data/SARS-COV-2'
    TAXON = 'SARS-CoV-2'
    ORGANISM = 'Severe acute respiratory syndrome coronavirus 2'
    GENBANK_DIR = os.path.join(BASEDIR, 'genbank')

