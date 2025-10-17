import pandas as pd
xls = pd.ExcelFile('Kd-Kp_2023-semestre1.xlsx')
df1 = pd.read_excel(xls, 'Kd-Kp').dropna()
df1['Date'] = df1['Date'].replace('-.*',':00',regex=True)
df1['Date'] = pd.to_datetime(df1['Date'],format='%d/%m/%Y %H:%M:%S') # 30/06/2023 23:00:00
df1.rename(columns={'Unnamed: 57':'Parc Nucléaire Complet'}, inplace=True)
df1.set_index('Date',inplace=True)
print(df1.info())
# Resample for complete daily df1 
df1 = df1.resample(rule='24H', closed='left', label='left').mean()
df1.index = pd.to_datetime(df1.index).date
df1['date'] = df1.index
print(df1)
df1.to_excel('Kd-Kp_2023-semestre1_daily.xlsx')
for column_name in [x for x in df1.columns if x!='date']:
    df_to_export = df1[['date',column_name]]
    print('Generate file '+'test_data/'+column_name+' 2023 H1.csv ...')
    df_to_export.to_csv('test_data/'+column_name+' 2023 H1.csv',sep=',',index=False)
    