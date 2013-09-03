# -*- coding: utf-8 -*-
'''
Created on May 31, 2013
@author: Tom Eaton

Overview:
This program converts the raw Amazon order extract XMLSS file into a 
ready-for-upload CSV readable by Everest.

Workflow:
1.  F Read master.xml
2.    Verify column heading labels
3.  F Filter in relevant data
4.  F Suppress special unicode characters
5.  F Generate PO line numbers
6.    Find matching Everest code
7.    Generate Price discrepancy spreadsheet
8.    Generate warnings, match UPC AND ASIN.
9.  F Generate import data csv
10. F Generate import header csv
11. F Add SLMTools to Git
12.   Web interface

-------------------------------------------------------------------------------
'''

import xml.etree.cElementTree as ET
import csv
import os
import datetime
import glob

# Functions
def removeNonASCII(x):
		return "".join(i for i in x if ord(i)<128)

def replaceBlankCode(row):
	pass

def readCSV(filename):
	dict = {}
	with open(filename, 'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			row[2] = row[2].translate(None, '() -x')
			dict.update({row.pop(0): row})
	del dict['First Name']
	return dict		

def writeCSV(filename, writetable):
	with open(filename, 'wb') as f:
		writer = csv.writer(f)
		writer.writerows(writetable)	

# Open XMLSS file at Line Items worksheet
os.chdir(os.path.dirname(__file__))
ifile = glob.glob("AmazonPOs*")[0]
tree = ET.parse(ifile)
root = tree.getroot()
line_items = root[4][0]

# Column headings
log_head    = ['PO', 'Deliver', 'Warehouse', 'Line', 'UPC', 'Code', 'Description', 'Qty', 'Cost']
data_head   = ['Order ID', 'Line ID', 'Product ID', 'Product Code', 'Quantity', 'Unit Price']
header_head = ['OrderID', 'Date', 'NumericTime', 'ShipName', 'ShipaAddress1', 'ShipAddress2', 
               'ShipCity', 'ShipState', 'Ship Country', 'Ship Zip', 'ShipPhone', 'Bill Name', 
			   'Bill Address 1', 'Bill Address 2', 'Bill City', 'Bill State', 'Bill Country', 
			   'Bill Zip', 'Bill Phone', 'Email',	'Referring Page', 'Entry Point', 'Shipping', 
			   'Payment Method', 'Card Number', 'Card Expiry', 'Comments', 'Total', 'Link From', 
			   'Warning', 'Auth Code', 'AVS Code', 'Gift Message']

# Generic header data
header_template = ['PO Number', 'Date', '','Ship Name', 'Ship Address', 'Ship Address 2', 'Ship City', 'Ship State', 'US United States', 
				   'Ship Zip', 'Ship Phone', 'Amazon', 'ACCOUNTS PAYABLE', 'PO BOX 80387', 'SEATTLE', 'WA', 
			       'US United States', '98108', '2062662335', 'ap-missing-invoices@amazon.com', '', 
			       '', 'UPS', 'CHECK', '', '', '']
				   
# Relevant columns to keep
keep_cols  = [0, 1, 2, 4, 7, 8, 13, 22] # Keep from original file
log_cols   = [0, 6, 7, 8, 1, 2, 3, 5, 4] # New order for log file
data_cols  = [0, 8, 2, 2, 5, 4] # New order for data file

# Load order data into 2D list.
order_data = []
for row_count, row in enumerate(line_items.findall('{urn:schemas-microsoft-com:office:spreadsheet}Row')):
	new_row = []
	for col_count, cell in enumerate(row.iter('{urn:schemas-microsoft-com:office:spreadsheet}Cell')):
		for cell_data in cell.iter('{urn:schemas-microsoft-com:office:spreadsheet}Data'):
			if row_count >= 4 and col_count in keep_cols:
				if col_count == 2:
					new_row.append(cell_data.text)
				elif col_count == 4:
					new_row.append(removeNonASCII(cell_data.text))
				elif col_count == 7:
					new_row.append(float(cell_data.text.translate(None, '$, '))) # Remove special characters from price.
				elif col_count == 8:
					new_row.append(int(cell_data.text.translate(None, ', '))) # Remove special characters from quantity.
				elif col_count == 13:
					new_row.append(datetime.datetime.strptime(cell_data.text[:10], '%Y-%m-%d').strftime('%m/%d/%Y')) # Convert date
				else:
					new_row.append(cell_data.text)
	if new_row != []:
		order_data.append(new_row)
	
# Create dictionary [PO Number]: [Ship To, Order Total, Ship Date]
po_nums = []
po_data = {}
for i, cur_row in enumerate(order_data):
	new_row = []
	if not cur_row[0] in po_nums:
		po_nums.append(cur_row[0])
		po_data[cur_row[0]] = [cur_row[7], 0, cur_row[6]]

po_tally = 0
for i, cur_row in enumerate(order_data):
	po_tally += cur_row[4] * cur_row[5]
	po_data[cur_row[0]][1] += cur_row[4] * cur_row[5]	
	
# Calculate order totals & load destination location into dictionary
order_totals = {}
for po in po_nums:
	order_totals[po] = 0

po_tally = 0
for i, cur_row in enumerate(order_data):
	line_ext = float(cur_row[4]) * float(cur_row[5])
	po_tally += line_ext
	order_totals[cur_row[0]] += line_ext

# Add line items
for i, row in enumerate(order_data):
	if row[0] == order_data[i - 1][0]:
		row.append(order_data[i - 1][8] + 1)
	else:
		row.append(1)

# Create header table
ifile = os.path.dirname(__file__) + '\\resource\Amazon Shipping Address.csv'
shipping_info = readCSV(ifile)

header_data = []
for po in po_data:
	new_row = []
	header_template[0] = po
	header_template[1] = datetime.datetime.now().strftime('%m/%d/%Y')
	header_template[3] = po_data[po][0] + ' ' + shipping_info[po_data[po][0]][0]
	header_template[4] = shipping_info[po_data[po][0]][2]
	header_template[5] = shipping_info[po_data[po][0]][3]
	header_template[6] = shipping_info[po_data[po][0]][4]
	header_template[7] = shipping_info[po_data[po][0]][5]
	header_template[9] = shipping_info[po_data[po][0]][6]
	header_template[10] = shipping_info[po_data[po][0]][1]
	new_row.extend(header_template)
	new_row.append(po_data[po][1])
	header_data.append(new_row)	

# Parse data into data and log files
log_data = []
import_data = []
for i, cur_row in enumerate(order_data):
	import_row = []
	log_row = []
	for x in log_cols:
		log_row.append(cur_row[x])
	for x in data_cols:
		import_row.append(cur_row[x])
	log_data.append(log_row)
	import_data.append(import_row)
	
# Add header rows to data
log_data.insert(0, log_head)
import_data.insert(0, data_head)
header_data.insert(0, header_head)

# Write files		
dfile = os.path.dirname(__file__) + '\output\Amazon New Orders Data ' + datetime.datetime.now().strftime('%m-%d-%Y %I%M%p') + '.csv'
hfile = os.path.dirname(__file__) + '\output\Amazon New Orders Header ' + datetime.datetime.now().strftime('%m-%d-%Y %I%M%p') + '.csv'
lfile = os.path.dirname(__file__) + '\output\Amazon New Orders Log ' + datetime.datetime.now().strftime('%m-%d-%Y %I%M%p') + '.csv'
writeCSV(lfile, log_data)
writeCSV(dfile, import_data)
writeCSV(hfile, header_data)

print
print '-----------------------------------------------------------------------'
print
print 'New files generated: '
print dfile
print hfile
print lfile
print
print str(len(import_data) - 1) + ' order lines.'
print str(len(order_totals)) + ' new orders.'
print 'Total order value: $' + '{0:,.2f}'.format(po_tally)
print
print '-----------------------------------------------------------------------'