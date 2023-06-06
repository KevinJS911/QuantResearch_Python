# -*- coding: utf-8 -*-
"""
Created on Wed May 31 13:50:22 2023

@author: Kevin John Stanly
"""

import pandas as pd
from urllib.request import Request, urlopen
import sqlite3
import numpy as np
import os

#%%
###############################################################################
#Read/Specify Before Running Scripts:
'''Using this script, :
* you can choose to either scrape the data or upload it from your local directory (after saving a copy from an initial scrape)
* you can choose to only scrape the data, only produce the output (using data file saved on your local directory) OR BOTH
'''
###############################################################################
    
url= "https://www.fca.org.uk/publication/data/short-positions-daily-update.xlsx"

scrape_flag = True #True if you want to scrape the data; False if you want to upload it from local directory
process_flag = True #True if you want to produce output (False in case you want to only scrape/save the data) 
save_copy = True #True if you want to save a copy of raw historical data to local directory
output_flag = False #True if you want to save results in an excel file on local directory:

currWD = os.getcwd()
#Provide name of input file if you are uploading from local directory:
input_file_loc = currWD+'\\Historical_Data.xlsx'

#Provide name of copy (historical data):
raw_data_loc = currWD+'\\Historical_Data.xlsx' 

#%%Functions
###############################################################################   
# Function to calculate aggregated short positions and no of funds by ISIN and date
###############################################################################

def calculate_aggregated_short_positions(df):
    
    all_isins = np.unique(df["ISIN"])
    #Loop through each ISIN code
    aggData = pd.DataFrame()
    c_ =0
    for i in range(len(all_isins)):
        c=int(100*len(all_isins[:i])/len(all_isins))
        if (c_ != c):
            print ("Status: "+str(int(100*len(all_isins[:i])/len(all_isins)))+"% completed")
        c_=c
        currISIN = df[df["ISIN"]==all_isins[i]].sort_values(["Position Date"]).reset_index(drop=True)        
    
        #Creating df with size equal to no of business days from first date to last date (both inclusive) for the ISIN
        currAggData= pd.DataFrame()
        currAggData["Position Date"] = pd.bdate_range(currISIN["Position Date"][0].date(), currISIN["Position Date"][len(currISIN["Position Date"])-1].date())
        currAggData["ISIN"] = [all_isins[i] for x in range(len(currAggData))]
        currAggData["Aggregated Short"] = [0 for x in range(len(currAggData))]
        currAggData["Number of Funds"] = [0 for x in range(len(currAggData))]
        
        #For each holder, adding short position within date range
        for currHolder in list(np.unique(currISIN["Position Holder"])):
            x = pd.DataFrame(np.zeros((len(currAggData), 2)), columns=["Aggregated Short", "Number of Funds"])
            
            currHolder_Data = currISIN[currISIN["Position Holder"]==currHolder].reset_index(drop=True)
            #Initializing values for loop:
            start = [0]
            shortRate = 0
            flag = 1
            #Looping through each holder's dates (currISIN)
            for i in range(len(currHolder_Data)):
                stop = currAggData[currAggData['Position Date']==currHolder_Data['Position Date'][i]].index
                x["Aggregated Short"][start[0]: stop[0]] += [shortRate for x in range(start[0], stop[0])]
                
                if (flag != 1):
                    x["Number of Funds"][start[0]: stop[0]] += [1 for x in range(start[0], stop[0])]
                else:
                    flag =0
                shortRate =  currHolder_Data['Net Short Position (%)'][i]
                start = stop
    
            #Adding values for last disclosure:
            x["Aggregated Short"][start[0]] += [shortRate]
            x["Number of Funds"][start[0]] += 1            
            
            currAggData["Aggregated Short"] += x["Aggregated Short"]
            currAggData["Number of Funds"] += x["Number of Funds"] 
            
        aggData = pd.concat([aggData, currAggData])  

    return aggData

###############################################################################
# Storing aggregated short positions in database table
###############################################################################

def store_results(aggregated_data):
    conn = sqlite3.connect(currWD+"\\Results.db")
    aggregated_data.to_sql("results", conn, if_exists="replace")
    conn.execute(
        """
        create table my_table as 
        select * from results
        """) 

############################################################################### 
#Updating weekends to next business day
###############################################################################

def update_weekend_dates(df):
    df['Position Date'] = pd.to_datetime(df['Position Date'])
    mask = df['Position Date'].dt.dayofweek > 4
    df.loc[mask, 'Position Date'] += pd.to_timedelta((7 - df.loc[mask, 'Position Date'].dt.dayofweek) % 7, unit='D')
    return df

#%% 
###############################################################################
#Reads Data from either URL Link or Local Directory and if required, saves a copy from web scrape
###############################################################################

if (scrape_flag):
    req = Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.1'}
    )
    webpage = urlopen(req).read()
    raw_file_data = pd.read_excel(webpage, sheet_name = None)
    
    #Extract Historical Data
    historical_data = list(raw_file_data.values())[1]    
    print ("Successfully Scraped Excel File.")
    
    if (save_copy):
        historical_data.to_excel(raw_data_loc, index= False)

else:
    historical_data = pd.read_excel(input_file_loc)
    
    print ("Successfully Read Excel File from Local Directory")
    
#%% 
################################################################################
#Generating Output and Saves Results to DB/Excel File
###############################################################################

if (process_flag):
    
    #Some dates are weekends and since we want business days, updating Position Dates column:
    historical_data = update_weekend_dates(historical_data)    
    
    aggregated_data= calculate_aggregated_short_positions(historical_data)
    print ("Generated Results")
    
    #Removing rows with 0 disclosures (cases where no overlap between disclosures streams of any 2 holders)
    aggregated_data = aggregated_data[aggregated_data['Aggregated Short']!=0]    
    aggregated_data = aggregated_data[['ISIN','Position Date', 'Aggregated Short', 'Number of Funds']]
    
    #Optional: Saving Results as excel file
    if (output_flag):
        aggregated_data.to_excel(currWD+"\\Results.xlsx", index= False)
        print ("Successfully Saved Results Excel File")
    
    #Storing Results in SQLite DB:
    store_results(aggregated_data)
    print('Results stored in the SQLite database.')    