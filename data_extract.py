# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 10:59:14 2017

@author: caoa
"""

import pandas as pd
import os

key = os.getenv('honda_gmap')
apikey = 'key={}'.format(key)

pd.options.display.max_rows = 16
pd.options.display.max_columns = 16

screenshot_flag = True # for wallpaper
update_fusion_table_flag = True # for website

#%% Read data
wdir = os.path.join('static','data')
filename1 = 'Customers.txt'
filename2 = 'Orders.txt'
filepath1 = os.path.join(wdir,filename1)
filepath2 = os.path.join(wdir,filename2)
cust = pd.read_csv(os.path.join(wdir,filename1), sep='|')
orders = pd.read_csv(os.path.join(wdir,filename2), sep='|')

#%%
orders = orders.loc[:,'TransID':'Zone']
orders['DateID'] = pd.to_datetime(orders['DateID'])
currency_columns = ['Selling Price','Comm','Transaction Fee','Closing Fee','Paypal Fee','Shipping Credit','Shipping Cost']
orders[currency_columns] = orders[currency_columns].applymap(lambda x: x.replace('($','-').strip('$)') ).astype(float)

#%% Merge customer and order table and tally sales by state
fa = orders.merge(cust, how='inner', on='ID')
fa.fillna("", inplace=True)
fa['full_address'] = fa.apply(lambda x: f"{x['Address']}, {x['City']} {x['State']}, {x['ZipCode']}", axis=1)
fa['full_address'] = fa['full_address'].apply(lambda x: x.strip(',').strip())
fa['DateID'] = fa['DateID'].dt.date

#%% Aggregate Sales Data
grps = fa.groupby(['State','Type'])
sales = grps.size().to_frame()
# Cast from long to wide format for javascript
sales.reset_index(inplace=True)
sales.columns = ['state','type','n']
sales = sales.pivot(index='state', columns='type', values='n')
sales = sales.fillna(0).astype(int)
sales.drop('', axis=0, inplace=True)

#%% Replace state abbreviation with full name
state_names = pd.read_csv(os.path.join(wdir,'state_abbreviation.txt'), sep='\t', index_col=0)
sales = state_names.merge(sales, how='left', left_index=True, right_index=True)
sales.set_index('state', inplace=True)
sales = sales.fillna(0).astype(int)
# Create Total column
sales['Total'] = sales.sum(axis=1)



#%% Create json file for gmap_choropleth_geojson_fusion_eventhandling.html
#with open(os.path.join(wdir,'statedata.js'),'w') as fout:
#    fout.write('var statedata = ')
#    sales.to_json(fout, orient='index')    

#%% Take screenshot
# You might need to update to the latest chromedriver.exe in the Anaconda3 folder
#if screenshot_flag:    
#    from selenium import webdriver
#    import time
#    
#    driver = webdriver.Chrome(r'C:\Users\caoa\AppData\Local\Continuum\Anaconda3\chromedriver.exe')
#    driver.set_window_size(1500,900)
#    # Make sure server is started in correct directory
#    # python -m http.server 8080
#    driver.get('localhost:8080/gmap_choropleth_geojson_fusion_eventhandling.html') # or 127.0.0.1:8080
#    time.sleep(1)
#    wallpaperdir = r'C:\Users\caoa\Desktop\wallpaper'
#    driver.get_screenshot_as_file(os.path.join(wallpaperdir,'choropleth.png'))
#    driver.quit()
