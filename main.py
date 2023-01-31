import requests
from string import Template
from bs4 import BeautifulSoup
from lxml import etree
import datetime
from joblib import Parallel, delayed
import csv
from itertools import chain

website = "https://phonedb.net/"

def get_spec(device_id:str) -> datetime.datetime :
    release_date = None
    try:
        URL = Template(website + "index.php")
        data = {'model': device_id}
        params = {'m': 'device','s': 'query'}
        page = requests.post(
            URL.template
            , data=data
            , params=params
            )
        soup = BeautifulSoup(page.content, "html.parser")
        containers = soup.find_all("div", class_="container")
        result_device_url = None
        for c in containers:
            _devices = c.find("div", class_="content_block_title")
            if _devices is None:
                continue
            _link = _devices.find("a", href=True)
            if _link is not None:
                result_device_url = _link['href']
                break
        page = requests.get(website + result_device_url)
        soup = BeautifulSoup(page.content, "html.parser")
        dom = etree.HTML(str(soup))
        release_date = dom.xpath(
            '/html/body/div[4]/div/table/'
            + 'tr[td[1]/strong/text() = "Released"]/td[2]/text()'
            )[0]
        if not isinstance(release_date, str):
            raise Exception("Release date is not found")
        try:
            release_date = datetime.datetime.strptime(release_date, '%Y %b %d')
        except Exception:
            release_date = datetime.datetime.strptime(release_date, '%Y %b')
    except Exception as e:
        print(f"Error in model {device_id}: {e}")
    return release_date

def get_device_lists(csv_file:str) -> list[str]:
    device_lists = None
    with open(csv_file) as _csv_file:
        csv_reader = csv.reader(_csv_file, delimiter=',')
        next(csv_reader, None) #to skip header
        device_lists = list(chain.from_iterable(csv_reader))
    return device_lists

def save_device_spec(
        device_specs:list[list]
        , csv_file:str = 'device_specs.csv'
        ) -> None:
    if not len(device_specs) > 0:
        return
    with open(csv_file, mode='w') as _csv_file:
        writer = csv.DictWriter(_csv_file, fieldnames=['device_model', 'release_date'])
        writer.writeheader()
        for spec in device_specs:
            _release_date = None
            if isinstance(spec[1], datetime.datetime):
                _release_date = spec[1].strftime("%Y-%m-%d")
            writer.writerow({
                'device_model': spec[0],
                'release_date': _release_date,
                })


device_lists = get_device_lists('device_model.csv')
release_dates = Parallel(n_jobs=3)(delayed(get_spec)(i) for i in device_lists)
result = list(zip(device_lists, release_dates))
save_device_spec(result)

print("finished")