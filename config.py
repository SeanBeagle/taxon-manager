import os


basedir = '/Strong/proj/.data/SARS-COV-2'
taxon = 'SARS-CoV-2'
organism = 'Severe acute respiratory syndrome coronavirus 2'
genbank_dir = os.path.join(basedir, 'genbank')
database = 'sqlite:///' + os.path.join(basedir, taxon + '.db')


