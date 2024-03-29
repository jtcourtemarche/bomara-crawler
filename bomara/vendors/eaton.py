from bomara.crawler import Crawler
import urllib
from bs4 import BeautifulSoup

def parse(self):
    # Get description & part number ---------------------------------->
    self.page['Meta']['description'] = self.soup.find(
        class_='module-product-detail-card__description').get_text().replace('\n', '')
    self.page['Meta']['part_number'] = self.soup.find(
        class_='module-product-detail-card__title').get_text().replace('\n', '')

    self.page['Meta']['img_url'] = self.soup.find('img',
        class_='rendition__image').get('data-src')
    self.page['Meta']['img_type'] = '.jpg'

    # Open specifications page
    data = urllib.request.urlopen('http://www.eaton.com/us/en-us/skuPage.{}.specifications.html'.format(self.page['Meta']['part_number']))

    self.tech_soup = BeautifulSoup(data.read(), 'html.parser')

    specs = self.tech_soup.find('div', class_='product-specifications')
    for spec in specs.find_all('div', class_='module-table'):
        self.page['Headers'].append(spec.find('h3', 'module-table__head').get_text())
        for row in spec.find_all('div', 'module-table__row'):
            cols = row.find_all('div', 'module-table__col')
            title = cols[0].get_text()

            if title == 'Runtime Graph':
                description = '<a target="_blank" href="http://eg.eaton.com/ups-battery-runtime/en-us/{}">View Runtime Graph</a>'.format(self.page['Meta']['part_number'])
            elif [x for x in self.ignored_headers if title == x] != []:
                continue
            else:
                description = cols[1].get_text().strip('\n')

            self.page['Techspecs'].append((title, description))
            self.page['Headers'].append('*')

# This handles the NEW Eaton website only ->

crawler = Crawler(
    # Vendor name
    vendor = 'Eaton',
    schema = {
        # Required
        'Meta': dict(),
        # Required
        'Techspecs': [],
        # Required
        'Headers': [],
    },
    # Ignored tech specs headers
    ignored_headers = ['Extended Service Plans', 'Certifications'],
    # Mostly APC exclusive
    software_identifiers = [],

    links=['eaton.com/*'],

    # Required returns: 
    #   self.page['Meta']['part_number', 'img_url', 'img_type']
    #   self.page['Techspecs', 'Headers']
    parser = parse,
)