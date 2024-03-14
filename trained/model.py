import os
import joblib
import sys
import pathlib
import pandas as pd

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from utils.utils import logger

# X labels: ['humidity', 'smoke', 'temp']
def load():
    logger.info("Loading model")
    file_path = os.path.join(os.getcwd(), 'm_model.pkl')
    return joblib.load(file_path)

def predict(model, data):
    predictions = model.predict(pd.DataFrame([data], columns=["humidity", "smoke", "temp"]))
    logger.info("Predicting %s -- %s" % ({ 'humidity': data[0], 'smoke': data[1], 'temp': data[2] }, predictions))
    if len(predictions) > 0:
        return predictions[0]
    return -1
