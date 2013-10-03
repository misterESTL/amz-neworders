# -*- coding: utf-8 -*-
# Created on May 31, 2013
# @author: Tom Eaton
#
# This is the business logic for incoming purchase orders from Amazon.
# Orders are converted from XMLSS format into Everest Advanced Edition
# 5.0 compatible CSV header and data files.

import xml.etree.cElementTree as ET
import csv
import os
import datetime


filetypes = [('Excel File', ('.xls'))]

title = 'Amazon New Order Conversion'
description =  "This program will convert Amazon's Excel (XMLSS) purchase " \
               "orders into the format required by Everest for import." \
               "\n\nChoose the sales order file in the top field and the " \
               "directory for the output files in the second field." \
               "\n\n::Press Convert when ready::"


class ConvertOrder():
    '''This class reads orders and converts them to Everest Advanced Edition \
    5.0 format'''

    def __init__(self, paths):
        self.inFile = paths[0]
        self.dFile = paths[1] + '\Amazon New Order Data ' + \
          datetime.datetime.now().strftime('%m-%d-%Y %I%M%p') + '.csv'
        self.hFile = paths[1] + '\Amazon New Order Header ' + \
          datetime.datetime.now().strftime('%m-%d-%Y %I%M%p') + '.csv'

        self.processOrder(self.inFile, self.dFile, self.hFile)


    def processOrder(self, iFile, oFile, hFile):
        self.statusText = 'Processing...'

        newOrder = self.readXMLSS(iFile)
        newOrder = self.removeNonData(newOrder)
        newOrder = self.filterData(newOrder)
        newOrder = self.addLineNums(newOrder)
        newOrder = self.addExtPrice(newOrder)
        everestData = self.buildEverestData(newOrder)
        
        orderTotals = self.calcOrderTotals(newOrder)
        orderTotals = self.addShipTo(orderTotals, newOrder)
        shipToInfo = self.getShipToInfo(orderTotals)

        everestHeader = self.buildEverestHeader(orderTotals, shipToInfo)

        self.writeCSV(oFile, everestData)
        self.writeCSV(hFile, everestHeader)


    def removeNonASCII(self, x):
        return "".join(i for i in x if ord(i)<128)


    def readXMLSS(self, inFile):
        tree = ET.parse(self.inFile)
        root = tree.getroot()
        lineItems = root[4][0]

        tagPrefix = '{urn:schemas-microsoft-com:office:spreadsheet}'
        rowTag = tagPrefix + 'Row'
        cellTag = tagPrefix + 'Cell'
        dataTag = tagPrefix + 'Data'

        orderData = []
        for row in lineItems.findall(rowTag):
            newRow = []
            for cell in row.iter(cellTag):
                for cellData in cell.iter(dataTag):
                    newRow.append(cellData.text)

            if newRow != []:
                orderData.append(newRow)

        return orderData


    def removeNonData(self, order):
        for x in range(4):
            del order[0]

        return order


    def filterData(self, orderData):
        keepCols  = [0, 1, 2, 3, 4, 7, 8, 13, 19]
        filteredData = []

        for rowCount, row in enumerate(orderData):
            newRow = []
            for colCount, cell in enumerate(orderData[rowCount]):
                if colCount in keepCols:
                    if colCount == 4:
                        newRow.append(self.removeNonASCII(cell))
                    elif colCount == 7:
                        newRow.append(float(cell.translate(None, '$, ')))
                    elif colCount == 8:
                        newRow.append(int(cell.translate(None, ', ')))
                    elif colCount == 13:
                        newRow.append(datetime.datetime.strptime(cell[:10], \
                                      '%Y-%m-%d').strftime('%m/%d/%Y'))
                    else:
                        newRow.append(cell)

            if newRow != []:
                filteredData.append(newRow)

        return filteredData


    def addLineNums(self, order):
        for i, row in enumerate(order):
            row.insert(0, 1)
            if row[1] == order[i - 1][1]:
                row[0] = order[i - 1][0] + 1

        return order


    def addExtPrice(self, order):
        for row in order:
            row.insert(8, row[6] * row[7])

        return order


    def calcOrderTotals(self, order):
        totals = {}
        for row in order:
            if row[1] in totals:
                totals[row[1]] += row[8]
            else:
                totals[row[1]] = row[8]

        return totals


    def addShipTo(self, totals, order):
        shipInfo = {}
        for row in order:
            shipInfo[row[1]] = [totals[row[1]], row[10]]

        return shipInfo

    def buildEverestData(self, order):
        data = [['Order ID', 'Line ID', 'Product ID','Product Code',
                        'Quantity', 'Unit Price']]

        for row in order:
            newRow = [''] * 6
            for i, cell in enumerate(row):
                if i == 0:
                    newRow[1] = cell
                elif i == 1:
                    newRow[0] = cell
                elif i == 3:
                    newRow[2] = cell
                    newRow[3] = cell
                elif i == 6:
                    newRow[5] = cell
                elif i == 7:
                    newRow[4] = cell
            data.append(newRow)

        return data


    def buildEverestHeader(self, data, shipInfo):
        head = [['OrderID', 'Date', 'NumericTime', 'ShipName', 'ShipaAddress1',
                'ShipAddress2', 'ShipCity', 'ShipState', 'Ship Country',
                'Ship Zip', 'ShipPhone', 'Bill Name', 'Bill Address 1',
                'Bill Address 2', 'Bill City', 'Bill State', 'Bill Country',
                'Bill Zip', 'Bill Phone', 'Email', 'Referring Page',
                'Entry Point', 'Shipping', 'Payment Method', 'Card Number',
                'Card Expiry', 'Comments', 'Total', 'Link From', 'Warning',
                'Auth Code', 'AVS Code', 'Gift Message']]

        for order, details in data.iteritems():
            mmddyyyy = datetime.datetime.now().strftime('%m/%d/%Y')
            shDetails = shipInfo[order]
            
            newRow = [order, mmddyyyy, '', shDetails[0], shDetails[3], 
                shDetails[4], shDetails[5], shDetails[6], 'US United States',
                shDetails[7], shDetails[2], 'Amazon','ACCOUNTS PAYABLE',
                'PO BOX 80387', 'SEATTLE', 'WA', 'US United States', '98108',
                '2062662335', 'ap-missing-invoices@amazon.com', '', '', 'UPS',
                'CHECK', '', '', '', shDetails[8], '', '', '', '', '']
            head.append(newRow)
        return head
        

    def getShipToInfo(self, data):
        sFile = os.path.dirname(__file__)[:-4] 
        sFile += '\\resource\\Amazon Shipping Address.csv'
        shipDict = self.readCSV(sFile)
        
        poShipInfo = {}
        for po, details in data.iteritems():
            x = details[1]
            poShipInfo[po] = [x]
            for info in shipDict[x]:
                poShipInfo[po].append(info)
            poShipInfo[po].append(details[0])

        return poShipInfo


    def readCSV(self, filename):
        dict = {}
        with open(filename, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                row[2] = row[2].translate(None, '() -x')
                dict.update({row.pop(0): row})
        del dict['First Name']
        return dict     


    def writeCSV(self, filename, table):
        with open(filename, 'wb') as f:
            writer = csv.writer(f)
            writer.writerows(table)    