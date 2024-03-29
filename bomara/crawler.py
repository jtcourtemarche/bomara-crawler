#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib.request, urllib.error, urllib.parse
import json
import os
import copy
from jinja2 import Template, Environment, PackageLoader, select_autoescape
from bs4 import BeautifulSoup
from .utils import log
from pdf2image import convert_from_path
from shutil import copyfile

#
# Crawler()
# --------------------------------------------------------
# See example below
#
# Crawler().connect()
# --------------------------------------------------------
# Required: link to APC page
#
# Crawler().apply()
# --------------------------------------------------------
#

""" Example
crawler = Crawler(
    # Vendor name
    vendor = 'APC',
    schema = {
        # Required
        'Meta': dict(),
        # Required
        'Techspecs': [],
        # Required
        'Headers': [],
        # Optional
        'Options': {
            'Accessories': [],
            'Services': [], 
            'Software': []
        }
    },
    # Ignored tech specs headers
    ignored_headers = ['Extended Run Options', 'PEP', 'EOLI'],
    # Mostly APC exclusive
    software_identifiers = ['software', 'struxureware'],

    # Required returns: 
    #   self.page['Meta']['part_number', 'img_url', 'img_type']
    #   self.page['Techspecs', 'Headers']
    parser = parser(),
)
"""

class Crawler:
    def __init__(
        self, vendor, schema, links, parser, parser_args=[], ignored_headers=[], software_identifiers=[]):

        # Initializers
        self.vendor = vendor
        self.schema = schema
        self.links = links
        self._parser = parser
        self._parser_args = parser_args
        self._ignored_headers = ignored_headers
        self._software_identifiers = software_identifiers
        self.page = schema

        # Constants
        self.user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        self.breadcrumbs = []

        self.reset()

    def reset(self):
        self.page = copy.deepcopy(self.schema)

        self.parser_warning = None
        self.page['Meta']['vendor'] = self.vendor

        self.ignored_headers = self._ignored_headers
        self.software_identifiers = self._software_identifiers

        self.breadcrumbs = []

        self.parse = self._parser
        self.soup = None

    def dl_img(self, url, img_type, name):
        try:
            request = urllib.request.Request(url, None, {
                'User-Agent': self.user_agent
            })
            data = urllib.request.urlopen(request)

            # Create image directory if it doesn't exist already
            if not os.path.exists('output/images'):
                os.makedirs('output/images')

            name = name.replace(' ', '').replace('/', '-')

            with open('output/images/{0}{1}'.format(name, img_type), 'wb') as img_f:
                img_f.write(data.read())
                img_f.close()
            
            if img_type == '.pdf':
                # PDF Conversion
                pdf = convert_from_path('output/images/{}-drawing.pdf'.format(self.page['Meta']['part_number']), last_page=1, output_folder='output/images/', fmt='jpg')
                os.remove('output/images/{}-drawing.pdf'.format(self.page['Meta']['part_number']))
                # Rename random string filename to part number
                file_name = self.page['Meta']['part_number'] + '-drawing'

                # Append number saying which number drawing it is from the family
                n = os.listdir('output/images').count(file_name)

                if n != 0:
                    file_name = file_name + str(n) + self.page['Meta']['img_type']
                else:
                    file_name = file_name + self.page['Meta']['img_type']

                # Copy to proper name
                copyfile(pdf[0].fp.name, 'output/images/' + file_name)
                
                drawing = f'<img src="images/{file_name}" width="400" class="display-image"></img>'

                return drawing

            return True
        except urllib.error.URLError:
            return "Error loading image URL"
        except Exception as e:
            return "Image file download failed: {0!s}".format(e)

    def connect(self, url):
        # Connect
        p = False
        for l in self.links:
            if l.split('*')[0] in url:
                p = True
                
        if not p:
            raise ValueError('Not using the correct parser for this link')

        try:
            request = urllib.request.Request(url, None, {
                'User-Agent': self.user_agent
            })
            data = urllib.request.urlopen(request)
        except urllib.error.URLError:
            raise ValueError("Not a valid url!")

        if (data.getcode() != 200):
            raise ValueError('Error: {0!s}'.format(data.getcode()))
            
        html = data.read()
        self.soup = BeautifulSoup(html, 'lxml')   

    def cleanup(self, ids):
        for sid in ids:
            try:
                sid = sid.split('/')
                string = self.page[sid[0]][sid[1]] 

                if sid == 'part_number':
                    # Empty out spaces
                    string = string.replace(' ', '')

                string = string.replace('\t', '')
                string = string.replace('\n', '')
                string = string.replace(u'\u00ae', '')

                self.page[sid[0]][sid[1]] = string
            except:
                continue
        # Return last string for single usage
        return string

    def apply(self, template='base.html', write=False, parse=True, dl_img=True, breadcrumbs=None):
        if breadcrumbs:
            self.breadcrumbs = breadcrumbs

        if parse:
            try:
                self.parse(self)
            except Exception as e:
                raise ValueError('Failed to parse: {}'.format(e))

        # Cleanup part number & description
        self.cleanup(['Meta/part_number', 'Meta/description', 'Meta/includes'])

        # Write provides a JSON data sheet
        if write:
            output = json.dumps(self.page, sort_keys=True, indent=4)
            with open('output/output.json', 'w') as f:
                f.write(output)
                f.close()

        # Download part image
        if dl_img:
            img = self.dl_img(
                # URL
                self.page['Meta']['img_url'],
                # Image type
                self.page['Meta']['img_type'],
                # Name
                self.page['Meta']['part_number']
            )
            if img != True:
                self.parser_warning = str(img)

        # Breadcrumbs 
        if breadcrumbs != []:
            try:
                # Iterate through every 2 items in self.breadcrumbs
                breadcrumbs = [f"<a href='{self.breadcrumbs[x+1]}'>{self.breadcrumbs[x]}</a> » " for x in range(0, len(self.breadcrumbs), 2)]
                self.page['Meta']['breadcrumbs'] = ''.join(breadcrumbs)
            except Exception as e:
                self.parser_warning(f'Invalid breadcrumbs {e}')
                breadcrumbs = []
        self.env = Environment(
            loader=PackageLoader('bomara', '../templates'),
            autoescape=True
        )

        # Checks if options needs to be passed as False
        if 'Options' not in self.schema:
            self.page['Options'] = False

        if '/' in self.page['Meta']['part_number']:
            output_name = self.page['Meta']['part_number'].replace('/', '-')
        else:
            output_name = self.page['Meta']['part_number']


        with open(f'output/{output_name}.htm', 'wb') as t:
            try:
                template = self.env.get_template(template)
            except Exception as e:
                t.close()
                raise ValueError('No template found. {} could not be crawled'.format(self.page['Meta']['part_number']))
                
            template = template.render(
                meta=self.page['Meta'],
                techspecs=list(zip(self.page['Techspecs'], self.page['Headers'])),
                options=self.page['Options']
            ).encode('utf-8')
            t.write(template)
            t.close()

        log(self.page['Meta']['part_number'])
        return self.page['Meta']['part_number']
