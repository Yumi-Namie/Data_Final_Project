import pandas as pd
from functions import remove_columns, change_nan_to_median, create_median_dict
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
from sklearn.preprocessing import RobustScaler, OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer, make_column_selector
import numpy as np

df_madrid = pd.read_csv('airbnb_madrid_clean.csv')

##first we remove the columns that won't be used in the linear model
df_madrid = remove_columns(['Host ID', 'Host Name', 'Street', 'Neighbourhood Cleansed', 'City', 'State', 'Bed Type', "Amenities Rating",
'Country', 'Latitude', 'Longitude', 'ID', 'Number of Reviews', 'Host Identity Verified', 'Neighbourhood Group Cleansed'], df_madrid)

important_amenities = ['Kitchen', 'Internet', 'Air conditioning', 'Heating', 'Washer', 
'Dryer', 'Elevator', 'Wheelchair accessible', 'TV', 'Pool', '24-hour check-in']

df_madrid = remove_columns(important_amenities, df_madrid)
df_madrid.drop(df_madrid.columns[0], axis=1, inplace= True)

for index in range(len(df_madrid)):
    if df_madrid['Host Is Superhost'].iat[index]:
        df_madrid['Host Is Superhost'].iat[index] = 1
    else:
        df_madrid['Host Is Superhost'].iat[index] = 0

index_list = []
for index in range(len(df_madrid)):
    if not pd.isnull(df_madrid["Zipcode"].iat[index]):
        if "\n" in df_madrid['Zipcode'].iat[index]:
            print(df_madrid['Zipcode'].iat[index])
            index_list.append(index)

list_tuples=[(659, "28012"), (8056, "28051"), (8828, "28002")]
for tuple in list_tuples:
    index = tuple[0]
    zipcode = tuple[1]
    df_madrid['Zipcode'].iat[index] = zipcode

# df_madrid.loc[(df_madrid['Zipcode'] == '28051\n28051'), 'Zipcode'] = '28051'
# print('#################')
print(df_madrid[df_madrid['Zipcode'] == '28051\n28051'])

##now we divide in train and test
#train, test = train_test_split(df_madrid, test_size=0.2, random_state=40)

#train = train.dropna(subset=['Beds', 'Bathrooms', 'Bedrooms', 'Price', 'Review Scores Rating', 'Host Response Rate'])
#test= test.dropna(subset=['Beds', 'Bathrooms', 'Bedrooms', 'Price', 'Review Scores Rating', 'Host Response Rate'])

#y_train = train['Price']
#X_train = train.drop('Price', axis=1)
#y_test = test['Price']
#X_test = test.drop('Price', axis = 1)

#print(f'"Partición de entrenamento"\n-----------------------\n{y_train.describe()}')

#print(f'"Partición de test"\n-----------------------\n{y_test.describe()}')


##then we make dummie variables for the categorical columns
cat_columns = ['Property Type', 'Room Type', 'Cancellation Policy', 'Zipcode']

#for col in cat_columns:
    #one_hot = pd.get_dummies(X_train[col])
    #X_train = X_train.drop(col, axis=1)
    #X_train = X_train.join(one_hot)  

#for col in cat_columns:
    #one_hot = pd.get_dummies(X_test[col])
    #X_test = X_test.drop(col, axis=1)
    #X_test = X_test.join(one_hot)

for col in cat_columns:
    one_hot = pd.get_dummies(df_madrid[col])
    df_madrid = df_madrid.drop(col, axis=1)
    df_madrid = df_madrid.join(one_hot)

##now we divide in train and test
train, test = train_test_split(df_madrid, test_size=0.2, random_state=40)


##now we will deal with missing values and outliers in the train set
##first we remove the rows with nan values in beds, bathroms, bedrooms and price
train = train.dropna(subset=['Beds', 'Bathrooms', 'Bedrooms', 'Price', 'Review Scores Rating', 'Host Response Rate'])


##we need to deal with nan values in security deposit and cleaning fee
##we will use the median considering the number of rooms
number_of_rooms = train['Bedrooms'].unique()

dict_sd = create_median_dict(train, 'Bedrooms', 'Security Deposit', number_of_rooms)
dict_cf = create_median_dict(train, 'Bedrooms', 'Cleaning Fee', number_of_rooms)

for index in range(len(train)):
    change_nan_to_median(train, 'Bedrooms', 'Security Deposit', index, dict_sd)
    change_nan_to_median(train, 'Bedrooms', 'Cleaning Fee', index, dict_cf)


##cleaning outliers
train = train[train['Bedrooms'] <= 5]
train = train[(train['Bathrooms'] >= 1) & (train['Bathrooms'] <= 3)]
train = train[train['Accommodates'] <= 8]
train = train[train['Guests Included'] <= 6]

##We obtained these values in the lists from the file graphs.py, analyzing the data with a boxplot
bedrooms_price = [(0,110), (1,125), (2,200), (3,280), (4,390), (5,500)]
bathrooms_price = [(1,140), (1.5,180), (2,270), (2.5,330), (3,450)]
accommodates_price = [(1,60), (2,100), (3,120), (4,140), (5,180), (6,210), (7,270), (8,300)]
guests_included_price = [(1, 125), (2, 135), (3, 150), (4,220), (5,230), (6,300)]

dict_columns = {'Bedrooms' : bedrooms_price, 'Bathrooms': bathrooms_price, 'Accommodates': accommodates_price, 
'Guests Included': guests_included_price}

for column_name in dict_columns.keys():
    list_prices = dict_columns[column_name]
    for i in range(len(list_prices)):
        train = train[(train[column_name] != list_prices[i][0]) | ((train[column_name] == list_prices[i][0]) & (train['Price'] <= list_prices[i][1] ))]



total = train.isnull().sum().sort_values(ascending=False)
percent = (train.isnull().sum()/train.isnull().count()).sort_values(ascending=False)
missing_data = pd.concat([total, percent], axis=1, keys=['Total', 'Percent'])
print('missing data')
print(missing_data)


#now we deal with the nans in the test (if we have the time, make it into a pipeline)
##first we remove the rows with nan values in beds, bathroms, bedrooms and price
test = test.dropna(subset=['Beds', 'Bathrooms', 'Bedrooms', 'Price', 'Review Scores Rating', 'Host Response Rate'])

##we need to deal with nan values in security deposit and cleaning fee
##we will use the median from train considering the number of rooms
for index in range(len(test)):
    change_nan_to_median(test, 'Bedrooms', 'Security Deposit', index, dict_sd)
    change_nan_to_median(test, 'Bedrooms', 'Cleaning Fee', index, dict_cf)


y_train = train['Price']
X_train = train.drop('Price', axis=1)
y_test = test['Price']
X_test = test.drop('Price', axis = 1)

print(X_train.isna().sum().sort_values())

##this should work after removing Nans
lr = LinearRegression()
lr.fit(X_train, y_train)


##making predictions
y_pred = lr.predict(X_test)

_preds_df = pd.DataFrame(dict(observed=y_test, predicted=y_pred))
_preds_df.head()

# ##evaluating the model
print('MSE: {}'.format(mean_squared_error(y_test, y_pred)))
print('Mean Percentual Error: {}'.format(mean_absolute_percentage_error(y_test, y_pred)))


# ##random forest for comparison
rf = RandomForestRegressor()
rf.fit(X_train, y_train)

y_pred_rd = rf.predict(X_test)

print('Mean Percentual Error (RF): {}'.format(mean_absolute_percentage_error(y_test, y_pred_rd)))