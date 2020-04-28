import requests


URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'


def search(cls, db, organism, retmax=0):
    fcgi = 'esearch.fcgi'
    params = f"?db={db}&term=complete+genome+AND+{organism}[organism]&retmax={retmax}&retmode=json"
    url = f"{cls.URL}{fcgi}{params}"
    return requests.get(url)


def fetch(cls, db, id, rettype):
    fcgi = 'efetch.fcgi'
    params = f"?db={db}&id={id}&rettype={rettype}"
    url = f"{cls.URL}{fcgi}{params}"
    return requests.get(url)
