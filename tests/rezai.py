# main approach to merge data

import pandas as pd
from datetime import datetime
import time

cleaned_df = pd.read_csv("./tests/202507_JUL.csv")


cleaned_df = cleaned_df.loc[cleaned_df["unix"] < datetime(2025, 7, 1, hour=4 , minute=30).timestamp() * 1000]
cleaned_df.to_csv("2025-07f01t02.csv")
print(cleaned_df)

x = cleaned_df # input data

z = pd.DataFrame(columns=["unix","price","vol"]) # output
z = x.loc[[0]] # add first data

# init
trend = 0 # -> trend up => 1 , trend down => -1

t1 = time.time()
for index in range(0+1 ,x.shape[0]):
    prev_index = index-1
    last_z = z.index[-1]
    if trend > 0:
        if x.loc[index,"price"] >= x.loc[prev_index,"price"]:
            z.loc[last_z,'vol'] += x.loc[index,"vol"] # sum
            if x.loc[index,"price"] > x.loc[prev_index,"price"]:
                # update price and unix
                z.loc[last_z,'price'] = x.loc[index,"price"]
                z.loc[last_z,'unix']  = x.loc[index,"unix"]
        else: # current < prev 
            z = pd.concat([z,x.loc[[index]]],ignore_index=True) # insert new row (for new trend)                                                
            trend = -1

    elif trend < 0:
        if x.loc[index,"price"] <= x.loc[prev_index,"price"]:
            z.loc[last_z,'vol'] += x.loc[index,"vol"] # sum
            if x.loc[index,"price"] < x.loc[prev_index,"price"]:
                # update price and unix
                z.loc[last_z,'price'] = x.loc[index,"price"]
                z.loc[last_z,'unix']  = x.loc[index,"unix"]
        else: # current > prev
            z = pd.concat([z,x.loc[[index]]],ignore_index=True) # insert new row (for new trend)                                                
            trend = +1

    else: # trend = 0
        if x.loc[index,"price"] == x.loc[prev_index,"price"]:
            z.loc[last_z,'vol'] += x.loc[index,"vol"] # sum
        else:
            z = pd.concat([z,x.loc[[index]]],ignore_index=True) # insert new row            
            if x.loc[index,"price"] > x.loc[prev_index,"price"]:
                trend = 1
            elif x.loc[index,"price"] < x.loc[prev_index,"price"]:
                trend = -1
        

z.to_csv("./merged.csv",index=False)

t2 = time.time()

print(t2 - t1)