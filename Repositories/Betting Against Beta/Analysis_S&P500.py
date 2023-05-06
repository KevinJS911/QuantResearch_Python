# -*- coding: utf-8 -*-
"""
Spyder Editor
Author: Kevin John Stanly
This is a temporary script file.
"""
import pandas as pd
import matplotlib.pyplot as plt
#import datetime as dt
from dateutil.relativedelta import relativedelta
from scipy.stats import ttest_1samp
#import sklearn.linear_model as LinearRegression
import numpy as np

def ann_simple_ret(arr):
    ret=[]
    for date,price in arr.iterrows():
        date_12M = next12Months(date)
        try:
            price_12M = arr.loc[str(date_12M.date()),"S&P500"]
        except KeyError:
            price_12M= arr.loc[arr.loc[:,'dt'] < str(date_12M.date()),:]
            continue
        item=[date, price.loc["S&P500"], date_12M, price_12M,price_12M/price.loc["S&P500"]]        
        ret.append(item)
        df = pd.DataFrame(ret)
        df.columns = ["StartDate", "StartPrice", "EndDate", "EndPrice", "SimpleReturn"]
    return df

def next12Months(date):
    return date + relativedelta(months=12) + relativedelta(days = -1)

def prevday(arr, date):                        
    return date + relativedelta(days = -1)

##################################################################################

#PLEASE DEFINE BEFORE RUNNING:#
file_path = str("C:\\Users\\kevin\\OneDrive\\WORK\\LONDON BUSINESS SCHOOL\\Business Project (Research)\\Code\\")
sp500_file_name = "S&P 500 TR.csv"#S&P 500 TR.csv"#"SP500_Input.csv"
rfr_file_name = "box_gov_07302019.xlsx"
svixind_file_name = "index_svix_upd.csv"
crsp_file_name = "CRSP_Nagel.xlsx"
fed_file_name = "Livingstone_Data.xlsx"
conf_ind_file_name = "US_Confidence_Index.csv"

##################################################################################

##########################################Constructing Lower Bound
#Reading S&P500's SVIX2 data
svixind_raw_data = pd.read_csv(file_path+svixind_file_name)
svixind=svixind_raw_data.loc[:,["day", "month","year", "index.svix2"]]
cols=["month","day","year"]
svixind['date'] = svixind[cols].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
svixind=svixind.loc[:,['date', 'index.svix2']]
svixind['date'] = svixind['date'].astype('datetime64[ns]')
svixind.set_index('date', inplace=True)

#Plotting SVIX^2 Rate:
plt.plot(svixind.loc[:,"index.svix2"], '-', ms=2, color="black")
plt.title("Strike of Simple Variance Swap")
plt.xlabel("Year")
plt.ylabel("SVIX^2")
plt.show()

#Reading 12-month RFRs from Dr. Marco's Paper (https://www.dropbox.com/s/4azld4rt7twjiny/box_gov_07302019.xlsx?dl=0)
rfr_raw_data = pd.read_excel(file_path+rfr_file_name)
rfr=rfr_raw_data.loc[:,["day", "month", "year", "box_12m"]]
cols=["month","day","year"]
rfr['date'] = rfr[cols].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
rfr['box_12m']=np.exp(rfr['box_12m']/100)
rfr=rfr.loc[:,['date', 'box_12m']]
rfr['date'] = rfr['date'].astype('datetime64[ns]')
rfr.set_index('date', inplace=True)
combined_data_lower_bound = pd.merge(svixind, rfr, left_index=True, right_index=True)

combined_data_lower_bound["box_12m_rate"]=np.log(combined_data_lower_bound["box_12m"])
combined_data_lower_bound["LowerBound"]=combined_data_lower_bound["index.svix2"]*combined_data_lower_bound["box_12m"]

#Plotting Box Rate:
plt.plot(combined_data_lower_bound.loc[:,"box_12m_rate"], '-', ms=2, color="black")
plt.title("12 Month Box Rate")
plt.xlabel("Year")
plt.ylabel("Rate")
plt.show()

#Plotting Lower Bound:
plt.plot(combined_data_lower_bound.loc[:,"LowerBound"], '-', ms=2, color="black")
plt.title("12 Month Lower Bound ")
plt.ylabel("Lower Bound")
plt.xlabel("Year")
plt.show()

##########################################

#Reading S&P500 daily stock prices 
sp500_raw_data = pd.read_csv(file_path+sp500_file_name)
sp500=sp500_raw_data.loc[:,["Day", "Month", "Year", "S&P500"]]
cols=["Month","Day","Year"]
sp500['date'] = sp500[cols].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
sp500=sp500.loc[:,['date', 'S&P500']]
sp500['date'] = sp500['date'].astype('datetime64[ns]')
sp500['dt']=sp500['date'].astype('datetime64[ns]')
sp500.set_index('date', inplace=True)

#Calculating Annual Simple Returns from Stock Prices
sp500_ret_raw = ann_simple_ret(sp500)
sp500_ret=sp500_ret_raw.loc[:,['StartDate', 'SimpleReturn']]
sp500_ret.set_index('StartDate', inplace=True)

#Combine all 3 series if dates exist in all 3
#RFR is the latest start date in 2004
#SVIX2 is the earliest end date in 2013
#Total ~110 rows in this date range i.e., from 2004 to 2013
combined_data = pd.merge(pd.merge(svixind, rfr, left_index=True, right_index=True), sp500_ret, left_index=True, right_index=True)

#Plotting Simple Returns:
plt.plot(combined_data.loc[:,"SimpleReturn"]-1, '-', ms=2, color="black")
plt.title("12 Month Returns of S&P500")
plt.ylabel("Return (Rt=St/S0-1)")
plt.xlabel("Year")
plt.show()

#Calculating Annual Excess Returns using RFRs
combined_data["ExcessReturns"]=combined_data["SimpleReturn"]-combined_data["box_12m"]

#Plotting Excess Returns:
plt.plot(combined_data.loc[:,"ExcessReturns"], '-', ms=2, color="black")
plt.title("12 Month Excess Returns")
plt.ylabel("Excess Returns")
plt.xlabel("Year")
plt.show()

#Calculating Lower Bound according to Martin
combined_data["LowerBound"]=combined_data["index.svix2"]*combined_data["box_12m"]

#Calculating Excess Returns - Lower Bound 
combined_data["ExcessReturns_LowerBound"]=combined_data["ExcessReturns"]-combined_data["LowerBound"]

#Plotting Excess Returns - Lower Bound:
plt.plot(combined_data.loc[:,"ExcessReturns_LowerBound"], "-", color="black")
plt.title("Excess Returns (S&P500 TR)-Lower Bound")
plt.axhline(y=0, color='b', linestyle='-')
plt.ylabel("Excess Returns - Lower Bound")
plt.xlabel("Year")
plt.show()         

"""#Calculating Mean Expected Excess Returns - Lower Bounds
stats= combined_data.describe()
print (stats)

#Running t-Test to check if the mean is greater than from 0 ---- VALIDITY TEST
print(ttest_1samp(combined_data.loc[:,"ExcessReturns_LowerBound"], 0, alternative="greater"))
#Running t-Test to check if the mean is greater than from 0 ---- TIGHTNESS TEST
print(ttest_1samp(combined_data.loc[:,"ExcessReturns_LowerBound"], 0, alternative="two-sided"))"""


#Plotting distribution of Excess Returns - Lower Bounds:
plt.hist(combined_data.loc[:,"ExcessReturns_LowerBound"], bins=100, color='black')
plt.title("Histogram of Excess Returns - Lower Bound")
plt.ylabel("Frequency")
plt.xlabel("Excess Returns - Lower Bound")
plt.show() 

#Running regression between Excess Returns and Lower Bound
plt.scatter(combined_data.loc[:,"LowerBound"],combined_data.loc[:,"ExcessReturns"],marker=".", s=3)
plt.title("Excess Returns v/s Lower Bound")
plt.show() 

#Writing out csv output file
combined_data.to_csv(file_path+"Output_Files\\Output_SPX_TR.csv")

###############################################################################
#1. EXPECTATIONS - CRSP NAGEL DATA
#Reading CRSP quarterly expectation returns 
crsp_raw_data = pd.read_excel(file_path+crsp_file_name)
crsp=crsp_raw_data.loc[:,["Day", "Month", "Year", "stockexpret_NX"]]
cols=["Month","Day","Year"]
crsp['date'] = crsp[cols].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
crsp=crsp.loc[:,['date', 'stockexpret_NX']]
crsp['date'] = crsp['date'].astype('datetime64[ns]')
crsp['dt']=crsp['date'].astype('datetime64[ns]')
crsp.set_index('date', inplace=True)

#Combine CRSP, SVIX2 and RFR
combined_data_crsp = pd.merge(pd.merge(svixind, rfr, left_index=True, right_index=True), crsp, left_index=True, right_index=True)

#Calculating Simple Return from Returns
combined_data_crsp["SimpleReturn"]=combined_data_crsp["stockexpret_NX"]+1

#Calculating Annual Excess Returns using RFRs
combined_data_crsp["ExcessReturns"]=combined_data_crsp["SimpleReturn"]-combined_data_crsp["box_12m"]

#Calculating Lower Bound according to Martin
combined_data_crsp["LowerBound"]=combined_data_crsp["index.svix2"]*combined_data_crsp["box_12m"]

#Calculating Excess Returns - Lower Bound 
combined_data_crsp["ExcessReturns_LowerBound"]=combined_data_crsp["ExcessReturns"]-combined_data_crsp["LowerBound"]

#Plots:
plt.plot(combined_data_crsp.loc[:,"SimpleReturn"]-1, '-', ms=2, color='black')
plt.title("12 Month Expected Returns of CRSP Index")
plt.ylabel("Expected Return  (Rt=St/S0-1)")
plt.xlabel("Year")
plt.show()

plt.plot(combined_data_crsp.loc[:,"ExcessReturns"], "-", ms=2, color="black")
plt.title("12 Month Expected Excess Returns")
plt.ylabel("Expected Excess Returns")
plt.xlabel("Year")
plt.show()         

plt.plot(combined_data_crsp.loc[:,"ExcessReturns_LowerBound"], color ='black')
plt.title("Expected Excess Returns (CRSP Index)-Lower Bound")
plt.axhline(y=0, color='b', linestyle='-')
plt.ylabel("Expected Excess Returns - Lower Bound")
plt.xlabel("Year")
plt.show() 
"""
#Calculating Mean Expected Excess Returns - Lower Bounds
stats= combined_data_crsp.describe()
print (stats)

#Running t-Test to check if the mean is greater than from 0 ---- VALIDITY TEST
print(ttest_1samp(combined_data_crsp.loc[:,"ExcessReturns_LowerBound"], 0, alternative="greater"))
#Running t-Test to check if the mean is greater than from 0 ---- TIGHTNESS TEST
print(ttest_1samp(combined_data_crsp.loc[:,"ExcessReturns_LowerBound"], 0, alternative="two-sided"))
"""
#Writing out csv output file
combined_data_crsp.to_csv(file_path+"Output_Files\\Output_CRSP.csv")

plt.hist(combined_data_crsp.loc[:,"ExcessReturns_LowerBound"], bins=10, color='black')
plt.title("Histogram of Excess Returns - Lower Bound")
plt.ylabel("Frequency")
plt.xlabel("Excess Returns - Lower Bound")
plt.show() 

#Running regression between Excess Returns and Lower Bound
plt.scatter(combined_data_crsp.loc[:,"LowerBound"],combined_data_crsp.loc[:,"ExcessReturns"], color="black")
plt.title("Excess Returns v/s Lower Bound")
plt.ylabel("Lower Bound")
plt.xlabel("Excess Returns")
plt.show() 

###############################################################################
#2. EXPECTATIONS - PHILADELPHIA FED DATA
#Reading FED bi-yearly expectation returns 
fed_raw_data = pd.read_excel(file_path+fed_file_name)
fed=fed_raw_data.loc[:,["Day", "Month", "Year", "SimpleReturn"]]
cols=["Day","Month","Year"]
fed['date'] = fed[cols].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
fed=fed.loc[:,['date', 'SimpleReturn']]
fed['date'] = fed['date'].astype('datetime64[ns]')
fed['dt']=fed['date'].astype('datetime64[ns]')
fed.set_index('date', inplace=True)

#Combine FED, SVIX2 and RFR
combined_data_fed = pd.merge(pd.merge(svixind, rfr, left_index=True, right_index=True), fed, left_index=True, right_index=True)

#Calculating Annual Excess Returns using RFRs
combined_data_fed["ExcessReturns"]=combined_data_fed["SimpleReturn"]-combined_data_fed["box_12m"]

#Calculating Lower Bound according to Martin
combined_data_fed["LowerBound"]=combined_data_fed["index.svix2"]*combined_data_fed["box_12m"]

#Calculating Excess Returns - Lower Bound 
combined_data_fed["ExcessReturns_LowerBound"]=combined_data_fed["ExcessReturns"]-combined_data_fed["LowerBound"]

#Plots:
plt.plot(combined_data_fed.loc[:,"SimpleReturn"]-1, '-', ms=2, color="black")
plt.title("12 Month Expected Returns of S&P500 Index ")
plt.ylabel("Expected Return  (Rt=St/S0-1)")
plt.xlabel("Year")
plt.show()

plt.plot(combined_data_fed.loc[:,"ExcessReturns"], "-", ms=5, color="black")
plt.title("12 Month Expected Excess Returns (S&P500 Index)")
plt.ylabel("Expected Excess Returns")
plt.xlabel("Year")
plt.show()         

plt.plot(combined_data_fed.loc[:,"ExcessReturns_LowerBound"], color="black")
plt.title("Expected Excess Returns (S&P500 Index)-Lower Bound")
plt.axhline(y=0, color='b', linestyle='-')
plt.ylabel("Expected Excess Returns - Lower Bound")
plt.xlabel("Year")
plt.show()         


"""#Calculating Mean Expected Excess Returns - Lower Bounds
stats= combined_data_fed.describe()
print (stats)

#Running t-Test to check if the mean is greater than from 0 ---- VALIDITY TEST
print(ttest_1samp(combined_data_fed.loc[:,"ExcessReturns_LowerBound"], 0, alternative="greater"))
#Running t-Test to check if the mean is greater than from 0 ---- TIGHTNESS TEST
print(ttest_1samp(combined_data_fed.loc[:,"ExcessReturns_LowerBound"], 0, alternative="two-sided"))
"""
#Writing out csv output file
combined_data_fed.to_csv(file_path+"Output_Files\\Output_FED.csv")

plt.hist(combined_data_fed.loc[:,"ExcessReturns_LowerBound"], bins=10, color='black')
plt.title("Histogram of Excess Returns - Lower Bound")
plt.ylabel("Frequency")
plt.xlabel("Excess Returns - Lower Bound")
plt.show()

#Running regression between Excess Returns and Lower Bound
plt.scatter(combined_data_fed.loc[:,"LowerBound"],combined_data_fed.loc[:,"ExcessReturns"], color="black")
plt.title("Excess Returns v/s Lower Bound")
plt.ylabel("Lower Bound")
plt.xlabel("Excess Returns")
plt.show() 

###############################################################################
#3. 1 YEAR US STOCK MARKET CONFIDENCE INDEX
#Reading Confidence Index monthly index values
confind_raw_data = pd.read_csv(file_path+conf_ind_file_name)
confind=confind_raw_data.loc[:,["Day", "Month", "Year", "Institutional Index Value", "Investors Index Value"]]
cols=["Day","Month","Year"]
confind['date'] = confind[cols].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
confind=confind.loc[:,['date', "Institutional Index Value", "Investors Index Value"]]
confind['date'] = confind['date'].astype('datetime64[ns]')
confind['dt']=confind['date'].astype('datetime64[ns]')
confind.set_index('date', inplace=True)

#Running FED, US 1 year Conf Ind and CRSP 
plt.plot(confind.loc[:,"Institutional Index Value"], label ="Institutional Investors")
plt.plot(confind.loc[:,"Investors Index Value"], label ="Individual Investors")
plt.title("US Stock Market Confidence Index")
plt.ylabel("Confidence Index")
plt.xlabel("Year")
plt.legend(loc="lower left")
plt.show()  

#Correlation between US Confidence Indices and Lower Bound
compare_confind = pd.merge(combined_data, confind, left_index=True, right_index=True)
print (np.corrcoef(compare_confind.loc[:,"Investors Index Value"], compare_confind.loc[:,"LowerBound"]))
print (np.corrcoef(compare_confind.loc[:,"Institutional Index Value"], compare_confind.loc[:,"LowerBound"]))

#Plotting all 3 in same graph
fig, lb = plt.subplots()

color = 'tab:red'
lb.plot(compare_confind.loc[:,"LowerBound"], "-", ms=2, color="black", label ="Lower Bound")
lb.set_ylabel('Lower Bound')
lb.legend(loc="upper left")

cf = lb.twinx() 

color = 'tab:blue'
cf.plot(compare_confind.loc[:,"Investors Index Value"], "-", ms=2, label ="Individual")
cf.plot(compare_confind.loc[:,"Institutional Index Value"], "-", ms=2, label ="Institutional")
plt.title("1 Year US Confidence Index v/s Lower Bound")
cf.set_ylabel('1 Yr Confidence Index')
plt.legend(loc="upper right")
plt.show()  

compare_confind.to_csv(file_path+"Output_Files\\Conf_Index.csv")
"""
#Plotting in different graphs
plt.subplot(311)
plt.plot(compare_confind.loc[:,"Investors Index Value"], "-", ms=5)
plt.plot(compare_confind.loc[:,"Institutional Index Value"], "-", ms=5)
plt.title("1 Year US Confidence Index ")

plt.subplot(313)
plt.plot(compare_confind.loc[:,"LowerBound"], "-", ms=5, color="black")
plt.title("Lower Bound")
plt.show() """