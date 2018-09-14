from bomara.crawler import Crawler
import urllib
from bs4 import BeautifulSoup

def parse(self):
    # Get description & part number ---------------------------------->
    self.page['Meta']['description'] = self.soup.find('meta',
        attrs={'itemprop':'name'}).get('content').replace(' | Server Technology', '')

    breadcrumbs = self.soup.find('ul', class_='breadcrumb')
    self.page['Meta']['part_number'] = breadcrumbs.find_all('li')[-1].get_text()

    # Full description
    self.page['Meta']['includes'] = self.soup.find('div', id="panel1a").get_text()

    # Product image
    self.page['Meta']['img_url'] = self.soup.find_all('img',
        class_='lazyOwl')[0].get('data-src')

    self.page['Meta']['img_type'] = '.png'

    # Open specifications page
    """
    data = urllib.request.urlopen('http://www.eaton.com/us/en-us/skuPage.{}.specifications.html'.format(self.page['Meta']['part_number']))
    self.tech_soup = BeautifulSoup(data.read(), 'html.parser')

    specs = self.tech_soup.find('div', class_='product-specifications')
    for spec in specs.find_all('div', class_='module-table'):
        self.page['Headers'].append(spec.find('h3', 'module-table__head').get_text())
        self.page['Techspecs'].append('*')
        for row in spec.find_all('div', 'module-table__row'):
            title = row.find_all('div', 'module-table__col')[0].get_text()

            if title == 'Runtime Graph':
                description = '<a target="_blank" href="http://eg.eaton.com/ups-battery-runtime/en-us/{}">View Runtime Graph</a>'.format(self.page['Meta']['part_number'])
            elif filter(lambda x: title == x, self.ignored_headers):
                continue
            else:
                description = row.find_all('div', 'module-table__col')[1].get_text().strip('\n')

            self.page['Techspecs'].append((title, description))
            self.page['Headers'].append('*')
    """

# This handles the NEW Eaton website only ->

crawler = Crawler(
    # Vendor name
    vendor = 'Servertech',
    schema = {
        # Required
        'Meta': dict(),
        # Required
        'Techspecs': [],
        # Required
        'Headers': [],
    },
    # Ignored tech specs headers
    ignored_headers = [],
    # Mostly APC exclusive
    software_identifiers = [],

    links=['servertech.com/families/*'],

    # Required returns: 
    #   self.page['Meta']['part_number', 'img_url', 'img_type']
    #   self.page['Techspecs', 'Headers']
    parser = parse,
)