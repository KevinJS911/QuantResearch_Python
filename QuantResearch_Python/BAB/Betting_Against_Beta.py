import pandas as pd
import numpy as np
from scipy import stats
import datetime as dt
from dateutil.relativedelta import relativedelta
import openpyxl

import warnings
warnings.filterwarnings("ignore")

def price2returns(price):
    ret = np.log(price[1:].reset_index()/price[:-1].reset_index())
    return ret.iloc[:,1]

def calcBeta(comp_name,x,y):
    y = list(y)
    x = list(x)
    result = stats.linregress(x,y)
    adj_beta = 0.6*result.slope+ 0.4
    #cov = np.cov(x,y)
    #beta.update({comp_name:cov[0,1]/cov[0,0]}) # included for checking if slope coefficient is correct
    if adj_beta >0:
        beta.update({comp_name:adj_beta})
    return 

def calcWeights(x, string): 
    all_weights = []
    pf_no = split/2
    denom = pf_no *(pf_no +1)/2
    w = []
    for i in range(1,int(pf_no)+1):
        w.append(i)
    i =0
    for comp in x:
        if string == "Low":
            w.sort(reverse=True)
            item = [comp[0], comp[1], w[i]/denom]
        else:
            item = [comp[0], comp[1], w[i]/denom]
        i = i+1 
        all_weights.append(item)
    return all_weights

def next12Months(date):

    return date + relativedelta(months=12) + relativedelta(days = -2)

def nextTradeDate(date): #This will return 12 Months (training) + 1 Month (trade) date for the input date
    
    return date + relativedelta(months=13) + relativedelta(days = -2)

def next1Month(date):
    if (date.month ==12):
        end = dt.datetime(date.year+1, 1, date.day)
    else:
        end = date + relativedelta(months=1)
    return end

def startofMonth(date):

    return dt.datetime(date.year,date.month, 1).date()

def endofMonth(date):
    
    if (date.month ==12):
        end = dt.datetime(date.year, date.month, 31)
    else:
        end = dt.datetime(date.year, date.month+1, 1) + relativedelta(days=-1)
    return end

###################################################################
#DEFINE BEFORE RUNNING 

first_date = "01-01-2010"
last_date = "31-12-2019"
input_file = "SP500_Input.csv"

split = 200 #How many components do you want in your portfolio? eg: for 4 high Bs and 4 low Bs --> split = 8
save_portfolio = 1 # 1 if you want to save the portfolio to .txt and excel files

generate_portfolio = 0 # Equal to 1 if you want to generate the porfolio

calculate_returns = 1 # Equal to 1 if you want to calculate returns on the portfolio generated

###################################################################
fdate = dt.datetime.strptime(first_date, "%d-%m-%Y")
ldate = dt.datetime.strptime(last_date, "%d-%m-%Y")

##Importing prices data
daily_prices = pd.read_csv(input_file, sep=',', parse_dates=[['Year','Month', 'Day']], date_parser=lambda x: pd.to_datetime(x, format="%Y %m %d"))
daily_prices = daily_prices.rename(columns={'Year_Month_Day': 'Date'})

#Calculating returns for each index/company/commodity/future
daily_returns = pd.DataFrame([])

for col in daily_prices.iloc[:,daily_prices.columns !="Date"]:
    daily_returns[col] = price2returns(daily_prices[col])

dates =  daily_prices.iloc[1:, daily_prices.columns =="Date"].reset_index()
daily_returns["Date"] = dates.iloc[:]["Date"]
daily_returns.set_index("Date", inplace=False)
print (daily_returns)

#Creating Initial Trim for First 12 months + 1 month (for trading)
first_training_date = fdate.date() + relativedelta(days=1)
last_training_date = next12Months(first_training_date)
next_trading_date = startofMonth(nextTradeDate(first_training_date))
t = next_trading_date - ldate.date()
end_trading_date = startofMonth(next1Month(next_trading_date))

daily_returns['Date'] = pd.to_datetime(daily_returns['Date'])

portfolio = pd.DataFrame(columns = ["First Training Date", "Last Training Date", "Start of Trade", "End of Trade", "LowBeta", "Low Beta Portfolio", "Low Beta Portfolio Returns","HighBeta","High Beta Portfolio", "High Beta Portfolio Returns"])

with open('High_Low_Betas_By_Date.txt', 'w') as f:
    while t.days< 0:

        training_dates_range= (daily_returns['Date'] >= pd.to_datetime(first_training_date)) & (daily_returns['Date'] <= pd.to_datetime(last_training_date))
        training_daily_returns = daily_returns.loc[training_dates_range]  
        
        #Removing components with NANs/NAs in the training + trading period
        to_be_removed = []
        removing_nan_range = (daily_returns['Date'] >= pd.to_datetime(first_training_date)) & (daily_returns['Date'] <= pd.to_datetime(next_trading_date))
        removing_nan_comp =  daily_returns.loc[removing_nan_range]
        for col in removing_nan_comp.iloc[:][:len(removing_nan_comp.columns)-1]:       
            if removing_nan_comp[[col]].isnull().values.any() ==True:
                to_be_removed.append(col)
        training_daily_returns = training_daily_returns.drop(columns=to_be_removed)

        #Starting Process of Calculating Betas for Each Component
        index_name = training_daily_returns.columns[0]
        index_returns = training_daily_returns.iloc[:][index_name]
        index_returns

        beta = {}
        for col in training_daily_returns.iloc[:][:len(training_daily_returns.columns)-1]:
            if col not in ["Date", index_name] :
                comp_index_date = training_daily_returns[["Date", col, index_name]]
                comp_name = col
                calcBeta(col, comp_index_date[index_name], comp_index_date[col])
            
            #Calculating Betas of Stock/Commodity/Forward Based on Previous 12 Month(s)

            #Ordering of All Betas and Extracting Top and Bottom 
            ordered_beta = sorted(beta.items(), key=lambda item: abs(item[1]))
            low_beta = ordered_beta[:int(split/2)]  #Ideally want to extract top and bottom quintiles/deciles for High and Low Betas respectively
            high_beta = ordered_beta[-int(split/2):]

            #Assigning Weights to Each Component of Portfolio
            high_beta_comp = calcWeights(high_beta, "High")
            low_beta_comp = calcWeights(low_beta, "Low")

        #Constructing Porfolio on day 1 of next month (saving it in a df)
        portfolio = portfolio.append({"First Training Date":str(first_training_date),"Last Training Date":str(last_training_date),"Start of Trade":str(next_trading_date),"End of Trade":str(end_trading_date),"LowBeta":low_beta_comp , "HighBeta":high_beta_comp}, ignore_index = True)
        print (portfolio)

        #Revise training and trade period parameters for next iteration
        first_training_date = next1Month(first_training_date)
        first_training_date = startofMonth(first_training_date)
        last_training_date = next12Months(first_training_date)
        last_training_date = endofMonth(last_training_date)
        next_trading_date = nextTradeDate(first_training_date)
        next_trading_date = startofMonth(next_trading_date)
        end_trading_date = startofMonth(next1Month(next_trading_date))
        t = next_trading_date - ldate.date()

returns = []
cum_pf_return = float(1)
cum_total_return = []
low_b = []
high_b = []
low_b_return = []
high_b_return = []

#Compute returns of portfolio during each trading period
if calculate_returns ==1:
    for index, row in portfolio.iterrows():
        trading_dates_range_bool_start= (daily_prices['Date'] >= pd.to_datetime(row["Start of Trade"])) 
        trading_dates_range = daily_prices.loc[trading_dates_range_bool_start]  
        min_date = min(trading_dates_range["Date"])

        trading_dates_range_bool_end= (daily_prices['Date'] >= pd.to_datetime(row["End of Trade"])) 
        trading_dates_range = daily_prices.loc[trading_dates_range_bool_end] 
        max_date = min(trading_dates_range["Date"])
        price_monthstart= daily_prices.loc[(daily_prices['Date'] == pd.to_datetime(min_date))]
        price_monthend= daily_prices.loc[(daily_prices['Date'] == pd.to_datetime(max_date))]  

        #Calculating returns of low beta portfolio
        low_beta_pf_return =0 
        high_beta_pf_return = 0
        low_beta_pf_beta =0
        high_beta_pf_beta = 0
        for comp in row["LowBeta"]:
            price_start = list(price_monthstart.loc[:,comp[0]])
            price_end = list(price_monthend.loc[:,comp[0]])
            if (np.isnan(price_start) ==False) & (np.isnan(price_end) == False):   
                ret = price_end[0]/price_start[0] -1
                low_beta_pf_return = low_beta_pf_return + ret*comp[2] 

                #Calculating Beta of Low Beta Portfolio
                low_beta_pf_beta = low_beta_pf_beta+comp[1]*comp[2]
            

        #Calculating returns of high beta portfolio
        for comp in row["HighBeta"]:
            price_start = list(price_monthstart.loc[:,comp[0]])
            price_end = list(price_monthend.loc[:,comp[0]])
            if (np.isnan(price_start) ==False) & (np.isnan(price_end) == False):
                ret = price_end[0]/price_start[0] -1
                high_beta_pf_return = high_beta_pf_return + ret*comp[2] 
             
                #Calculating Beta of High Beta Portfolio
                high_beta_pf_beta = high_beta_pf_beta+comp[1]*comp[2]
            

        weight_low_beta_pf = 1/low_beta_pf_beta
        weight_high_beta_pf = 1/high_beta_pf_beta

        pf_return = -1*(high_beta_pf_return)*weight_high_beta_pf + (low_beta_pf_return)*weight_low_beta_pf
        returns.append(pf_return)
        cum_pf_return = cum_pf_return * (1+pf_return)
        low_b.append(low_beta_pf_beta)
        high_b.append(high_beta_pf_beta)
        low_b_return.append(low_beta_pf_return)
        high_b_return.append(high_beta_pf_return)

        cum_total_return.append(cum_pf_return)
    portfolio["Returns"]=returns
    portfolio["Cumulative Returns"]=cum_total_return
    portfolio["Low Beta Portfolio"] = low_b
    portfolio["High Beta Portfolio"] = high_b
    portfolio["Low Beta Portfolio Returns"] = low_b_return
    portfolio["High Beta Portfolio Returns"] = high_b_return

    #Compute returns of index - done for performance measurement (but for passive management tho!)
    index_returns = []
    cum_index_return = 1
    cum_total_index_return = []

    for index, row in portfolio.iterrows():
        trading_dates_range_bool_start= (daily_prices['Date'] >= pd.to_datetime(row["Start of Trade"])) 
        trading_dates_range = daily_prices.loc[trading_dates_range_bool_start]  
        min_date = min(trading_dates_range["Date"])

        trading_dates_range_bool_end= (daily_prices['Date'] >= pd.to_datetime(row["End of Trade"])) 
        trading_dates_range = daily_prices.loc[trading_dates_range_bool_end]  
        max_date = min(trading_dates_range["Date"])
        price_monthstart= daily_prices.loc[(daily_prices['Date'] == pd.to_datetime(min_date))]
        price_monthend= daily_prices.loc[(daily_prices['Date'] == pd.to_datetime(max_date))]
        price_start = list(price_monthstart.iloc[:,1])
        price_end = list(price_monthend.iloc[:,1])
        index_ret = price_end[0]/price_start[0] -1
        index_returns.append(index_ret)
        cum_index_return = cum_index_return * (1+index_ret)
        cum_total_index_return.append(cum_index_return)

    #portfolio["Index Returns"]=index_returns
    #portfolio["Cumulative Index Returns"]=cum_total_index_return

if save_portfolio ==1:
    with pd.ExcelWriter('All_Portfolios_SP500_200_2010_2019_Individual_PF.xlsx', mode='w') as writer:  
        portfolio.to_excel(writer, sheet_name='Weights', index = False)