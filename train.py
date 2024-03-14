import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import matplotlib.pyplot as plt
import sklearn.metrics as sm
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn import metrics
import joblib

DATA_PATH = 'iot_telemetry_data.csv'

""" Preprocessing """

data = pd.read_csv(DATA_PATH)
print(data.isnull().sum())
data.drop('ts',     inplace=True, axis=1)
data.drop('device', inplace=True, axis=1)
data.drop('co',     inplace=True, axis=1)
data.drop('light',  inplace=True, axis=1)
data.drop('lpg',    inplace=True, axis=1)

# Only use [motion, humidity, temp, smoke]
data['motion'] = data['motion'].astype('int')
data['smoke']  = data['smoke'] * 100.0

def _get_motion_data(_data, value):
    _line_x = []
    _line_y = []
    _line_z = []
    for _idx in range(0, data.__len__()):
        if _data['motion'][_idx] == value:
            _line_x.append(_data['humidity'][_idx])
            _line_y.append(_data['temp'][_idx])
            _line_z.append(_data['smoke'][_idx])
    return _line_x, _line_y, _line_z

def show_chart():
    lines = [
        {
            "humidity": [],
            "temp": [],
            "smoke": [],
            "value": 1,
            "name": "Take action"
        },
        {
            "humidity": [],
            "temp": [],
            "smoke": [],
            "value": 0,
            "name": "Not take action"
        }
    ]

    lines[0]['humidity'], lines[0]['temp'], lines[0]['smoke'] = _get_motion_data(data, lines[0]['value'])
    lines[1]['humidity'], lines[1]['temp'], lines[1]['smoke'] = _get_motion_data(data, lines[1]['value'])

    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot(111, projection='3d')
    # ax.scatter(lines[0]['humidity'], lines[0]['temp'], lines[0]['smoke'], c='blue', marker='o', label=lines[0]['name'])
    ax.scatter(lines[1]['humidity'], lines[1]['temp'], lines[1]['smoke'], c='red', marker='o', label=lines[1]['name'])

    ax.set_xlabel('Humidity (%)')
    ax.set_ylabel('Temperature (°C)')
    ax.set_zlabel('Smoke Level')
    plt.title('Humidity, Temperature, and Smoke Levels')

    plt.legend()
    plt.show()

show_chart()
""""""""""""""""""""""""""""""""""""""""""

""" RANDOM FOREST """
x_labels = [i for i in data.columns if i != 'motion']
y_labels = ['motion']
print("X labels: %s" % x_labels)
print("Y labels: %s" % y_labels)

x_data, y_data = data[x_labels], data[y_labels]
x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, train_size=0.8, random_state=123)

# Calculate oob error --> take the best
# oob_error = []
# rn_est = list(range(30, 205, 5))
# for i in rn_est:
#     clf = RandomForestClassifier(max_features='sqrt', oob_score=True, n_estimators=i, random_state=123)
#     clf.fit(x_train, y_train)
#     oob_err = 1 - clf.oob_score_
#     oob_error.append(oob_err)

# best_n_est = rn_est[oob_error.index(min(oob_error))]

# Show oob error
def show_oob_error():
    plt.figure(figsize=(10, 5))
    plt.plot(rn_est, oob_error, label='OOB error rate')
    plt.plot(best_n_est, min(oob_error), marker='o', color='red', label='ideal n estimator')
    plt.xlabel('n estimators', fontsize=18)
    plt.ylabel('OOB error rate', fontsize=18)
    plt.legend(loc='upper right', prop={'size': 10})
    plt.show()

# show_oob_error()
best_n_est = 5 # TODO remove
print("Best for OOB error %s" % best_n_est)

print("Training model with best OOB error")

RF_classifier = RandomForestClassifier(max_features='sqrt', oob_score=True, n_estimators = best_n_est)
RF_classifier.fit(x_train, y_train)
y_RF_pred = RF_classifier.predict(x_test)

def confusion_matrix():
    print('Accuracy=', round(metrics.accuracy_score(y_test, y_RF_pred), 2))
    c_m = metrics.confusion_matrix(y_test, y_RF_pred)
    plt.figure(figsize=(10, 5))
    sns.heatmap(c_m/np.sum(c_m), annot=True, cmap='Blues_r', fmt='.2%',
                xticklabels=['Take action', 'Not take action'],
                yticklabels=['Take action', 'Not take action'])
    plt.xlabel('Predicted labels', fontsize=18)
    plt.ylabel('True labels', fontsize=18)
    plt.show()

# confusion_matrix()

""" Save Model """
joblib.dump(RF_classifier, "m_model.pkl")


print("Loading")
model = joblib.load("m_model.pkl")
predicts = model.predict(x_test)

print(predicts)
print(type(x_test))