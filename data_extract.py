# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 10:59:14 2017

@author: caoa
"""

import pandas as pd
import os
import json
from itertools import chain
from collections import defaultdict
import networkx as nx
from networkx.algorithms import community

pd.options.display.max_rows = 16
pd.options.display.max_columns = 16

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
state_names = pd.read_csv(os.path.join(wdir,'state_fips_abbr.csv'), usecols=[0,2], index_col=1)
sales = state_names.merge(sales, how='left', left_index=True, right_index=True)
sales.set_index('name', inplace=True)
sales = sales.fillna(0).astype(int)
# Create Total column
sales['value'] = sales.sum(axis=1)

#%% csv long format for d3calendar
cal = orders[['DateID']].resample('D', on='DateID').count()
cal.columns = ['count']
cal.index.name = 'date'
cal.to_csv(os.path.join(wdir,'calendar.csv'))

#%% json format for treemap
# Recursive function
def make_child(df, name, dtype=float):
    tree = {'name': name, 'children':[]}
    for child in df.index.get_level_values(0).unique():
        if isinstance(df.index, pd.MultiIndex):
            branch = make_child(df[child], child, dtype)
            tree['children'].append(branch)
        else:
            leaf = {'name':child, 'value':df[child].astype(dtype)}
            tree['children'].append(leaf)            
    return tree

tree = fa.groupby(['Site','Type'])['Selling Price'].sum()
TREE = make_child(tree, 'Foster Abe', int)
with open(os.path.join(wdir,'treemap.json'),'w') as fout:
    json.dump(TREE, fout, indent=2, default=int)
    
#%% json format for zoomable treemap
state_dict = dict(zip(state_names.index,state_names['name']))
state_dict['AB'] = 'Alberta'
state_dict['ON'] = 'Ontario'
state_dict['QC'] = 'Quebec'
state_dict[''] = 'Other'

fastate = fa.replace({'State':state_dict})
columns = ['Site','Type','State','Shipping Method']
tree = fastate.groupby(columns)['Selling Price'].sum()
TREE = make_child(tree, 'Foster Abe', int)
with open(os.path.join(wdir,'zoomabletreemap.json'),'w') as fout:
    json.dump(TREE, fout, indent=2, default=int)
  
#%% sankey format
origin_dict = {'F':'Free','C':'Paid','N':'Wife','G':'Gift','A':'Friends'}      
sankey = fa.copy()
sankey['Shipping Method'].replace('','In Person', inplace=True)
sankey['Origin'].replace(origin_dict, inplace=True)

columns = ['Origin','Site','Type','Shipping Method']
list_nodes = []
for column in columns:
    list_nodes.append(list(set(sankey[column])) )
nodes = list(chain.from_iterable(list_nodes))

list_flows = []
for i in range(len(columns)-1):
    cols = columns[i:i+2]
    flow = sankey.groupby(cols)['TransID'].count()
    tmp = flow.reset_index()
    tmp.columns = ['source','target','value']
    list_flows.append(tmp)

df = pd.concat(list_flows, ignore_index=True)
# csv format for sankey
df.to_csv(os.path.join(wdir,'sankey.csv'), index=False)

# json format for sankey
data = {'nodes':[{'name':n} for n in nodes],
        'links':df.to_dict(orient='records')}
with open(os.path.join(wdir,'sankey.json'),'w') as fout:
    json.dump(data, fout, indent=2, default=int)
   
#%% csv format for choropleth
sales[['value']].to_csv(os.path.join(wdir,'choropleth.csv'))

#%%
counties = pd.read_csv(os.path.join(wdir,'zcta_county_rel_10.txt'), usecols=[0,1,2,12])
counties.sort_values(['ZCTA5','COPOP'], ascending=[True,False], inplace=True)
counties.drop_duplicates('ZCTA5', inplace=True)
counties['FIPS'] = counties.apply(lambda x: f"{x['STATE']:0>2}{x['COUNTY']:0>3}", axis=1)
america = cust[(cust['ZipCode'].notnull()) & (cust['Country'].isnull()) & (cust['State'].notnull())]
Cust = america.merge(counties[['ZCTA5','STATE','FIPS']], how='inner', left_on='ZipCode', right_on='ZCTA5')

#%%
FA = orders.merge(Cust, how='inner', on='ID')
cty = FA.groupby('FIPS')['STATE'].size().reset_index()
cty.columns = ['fips','value']
cty.to_csv(os.path.join(wdir,'choropleth_county.csv'), index=False)

#%% json for force-directed graph
columns = ['Site','State']
links = fa.groupby(columns).size()
L = links.reset_index()

data = defaultdict(list)
for source, target, value in zip(L['Site'],L['State'],L[0]):
    data['links'].append({'source':source, 'target':target, 'value':value})

from random import randint
nodes = set(L['Site']).union(set(L['State']))
for node in nodes:
    data['nodes'].append({'id':node, 'group':randint(1,5)})

wdir = r'C:\Users\caoa\Box Sync\d3js Examples\v5\forcedirect'
with open(os.path.join(wdir,'forcedirect.json'),'w') as fout:
    json.dump(data, fout, indent=2, default=int)

#%%
G = nx.Graph()
edgelist = list(zip(L['Site'],L['State'],L[0]))
G.add_weighted_edges_from(edgelist)
partition = community_louvain.best_partition(G)

#for source, target, value in zip(L['Site'],L['State'],L[0]):
#    G.add_edge(source, target, weight=value)


