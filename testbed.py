#tanks.loc['Kills'].idxmax(axis=0) returns top killer
#temp1 = tanks.sort_values(by = 'Last Game') -->
#temp2 = temp1.sort_values(by = 'Kills', ascending=False) returns kill leaderboard

import numpy as np
import pandas as pd
import datetime

def new_row(name):
    print(datetime.datetime.now().strftime("%x %X"))
    return pd.DataFrame({"Kills":[0], "Deaths":[0], "Wins":[0], "Losses":[0], "Last Game":[datetime.datetime.now().strftime("%x %X")]}, index = [name])

def check_leaderboard(name, df):
    print(df)
    print('{} is {} in overall kills'.format(name, make_ordinal(np.flatnonzero(df['index'] == name)[0] + 1)))

def make_ordinal(n):
    n = int(n)
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n) + suffix

d = {
    "Tanks":['John', 'Mark', 'Han'],
    "Kills":[3,3,5],
    "Deaths":[3,2,1],
    "Wins":[2,2,2],
    "Losses":[2,2,2],
    "Last Game":["04/10/21 00:00:00", "04/09/21 00:00:00", "04/11/21 00:00:00"]
}
df = pd.DataFrame(d)
df = df.set_index('Tanks')
#print(df)
df = df.append(new_row('Bob'))
#print(df)
#print(df.Kills.idxmax(axis=0)) returned top killer
check_leaderboard('Mark', df.sort_values(by = 'Last Game').sort_values(by = 'Kills', ascending=False).reset_index())
#print(df2.loc[lambda x: x['index'] == 'John'])

