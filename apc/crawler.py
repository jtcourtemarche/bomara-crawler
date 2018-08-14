#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import json
import re
import os
import apc.tools
from jinja2 import Template, Environment, PackageLoader, select_autoescape
from bs4 import BeautifulSoup

#
# APCCrawler() 
# -------------------------------------------------------- 
# Required: link to APC page
# Optional: breadcrumbs
# breadcrumbs => list of tuples for every breadcrumb
#
# APCCrawler().parse()
# --------------------------------------------------------
# Optional: write
# write => outputs parsing results to a json file (output.json)
#
# APCCrawler().apply_template()
# --------------------------------------------------------
# Optional: template_dir, output_dir
# template_dir => template file location
# output_dir => directory to generate files to
#

class APCCrawler:
	# Reads url passed into class, parses data sheet as json,
	# and applies that data, among other things, to a jinja2 template
	def __init__(self, url, breadcrumbs=[]):
		self.user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
		self.page = {
			'Meta': dict(),
			'Techspecs': [],
			'Headers': []
		}

		self.breadcrumbs = breadcrumbs
		self.techspecs_title_filters = ['Extended Run Options', 'PEP', 'EOLI']

		#  CONNECT ---------------------------------------------->
		try:
			self.request = urllib2.Request(url, None, {
				'User-Agent':self.user_agent
			})
			self.data = urllib2.urlopen(self.request)
		except:
			raise ValueError("Not a valid url!")

		if (self.data.getcode() != 200):
			raise ValueError('Error: {0!s}'.format(self.data.getcode()))
		#  ------------------------------------------------------>

		html = self.data.read()
		self.soup = BeautifulSoup(html, 'html.parser')
		
		self.page['Meta']['description'] = self.soup.find(class_='page-header').get_text()
		self.page['Meta']['part_number'] = self.soup.find(class_='part-number').get_text()

	def parse(self, write=False):
		# Parse tech specs ---------------------------------------------->
		page_div = self.soup.find('div', id='techspecs')
		techspecs = []
		for header in page_div.find_all('h4'):
			cheader = header.contents[0]
			cheader = cheader.replace('&amp;', '&')
		
			if self.page['Headers']:
				self.page['Headers'][len(self.page['Headers'])-1] = cheader
			else:
				self.page['Headers'].append(cheader)

			list_item = header.find_next_sibling('ul', class_='table-normal')
			for contents in list_item.find_all(class_='col-md-12'):
				for title in contents.find(class_='col-md-3 bold'):
					# Checks title filters 
					if map(lambda x: x, filter(lambda x: x in title, self.techspecs_title_filters)) != []:
						continue

					contents = contents.get_text(' ', strip=True).replace(title, '')
					
					self.page['Techspecs'].append((title, contents))
					self.page['Headers'].append('')

		# Get image ---------------------------------------------------->
		try:
			# Newer pages
			self.page['Meta']['image'] = 'http:{}'.format(self.soup.find_all(class_='img-responsive')[0].get('src'))
		except:
			# Applicable to some older pages
			self.page['Meta']['image'] = 'http:{}'.format(self.soup.find_all(id='DataDisplay')[0].get('src'))
			
		# Includes ----------------------------------------------------->
		product_overview = self.soup.find_all(id='productoverview')[0]

		# Default includes to none
		self.page['Meta']['includes'] = ''
		try:
			# Test for explicit reference to includes
			# -> Usually found in older pages
			self.page['Meta']['includes'] = self.soup.find(class_='includes').get_text()
		except:
			# Scan for includes instead
			for p in product_overview.find_all('p'):
				if 'Includes' in p.get_text():
					self.page['Meta']['includes'] = p.get_text()
					break

		self.page['Meta']['includes'] = re.sub('\s\s+', ' ', self.page['Meta']['includes']).replace(' ,', ',')

		# Write provides a JSON data sheet ----------------------------->
		if write:
			output = json.dumps(self.page, sort_keys=True, indent=4)
			with open('output.json', 'w') as f:
				tools.log('Writing {} to output.json'.format(self.page['Meta']['part_number']))
				f.write(output)
				f.close()

	def apply_template(self, template_dir='../templates/base.html', output_dir='output/'):
		# Download part image ------------------------------------------>
		try:
			request = urllib2.Request(self.page['Meta']['image'], None, {
				'User-Agent':self.user_agent
			})
			data = urllib2.urlopen(request)
			
			# Create image directory if it doesn't exist already
			if not os.path.exists('{0}images'.format(output_dir)):
				os.makedirs('{0}images'.format(output_dir))

			with open('{0}images/{1}.jpg'.format(output_dir, self.page['Meta']['part_number']), 'wb') as img_f:
				img_f.write(data.read())
				img_f.close()
		except:
			raise ValueError("Image file download failed")

		# Breadcrumbs -------------------------------------------------->
		if not self.breadcrumbs:
			self.page['Meta']['breadcrumbs'] = ''
		else:
			breadcrumbs = map(lambda x: u"<a href='{0}'>{1}</a> »".format(x[1], x[0]), self.breadcrumbs) 
			self.page['Meta']['breadcrumbs'] = ''.join(breadcrumbs)

		# Parse given template_dir variable ---------------------------->
		path_indices = template_dir.split('/')
		for var in enumerate(path_indices):
			if '.html' in var[1]:
				template_file = path_indices[var[0]]
				template_dir = template_dir.split(var[1])[0]

		self.env = Environment(
			loader=PackageLoader('apc', template_dir),
			autoescape=True
		)
		with open('{0}{1}.htm'.format(output_dir, self.page['Meta']['part_number']), 'w') as t:
			template = self.env.get_template(template_file)
			template = template.render(
				meta = self.page['Meta'],
				techspecs = zip(self.page['Techspecs'], self.page['Headers']),
				# Not used in template currently deprecated
				options = False
			).encode('utf-8')
			t.write(template)
			t.close()
		apc.tools.log('Created: '+self.page['Meta']['part_number'])
		return self.page['Meta']['part_number']
