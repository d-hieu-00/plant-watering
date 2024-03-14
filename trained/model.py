import os
import joblib
import sys
import pathlib
import pandas as pd
import random

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from utils.utils import logger

# X labels: ['humidity', 'smoke', 'temp']
def load():
    logger.info("Loading model")
    file_path = os.path.join(os.getcwd(), 'm_model.pkl')
    return joblib.load(file_path)

def predict(model, data):
    predictions = model.predict(pd.DataFrame([data], columns=["humidity", "smoke", "temp"]))
    logger.info("Predicting %s -- %s" % ({ 'humidity': data[0], 'soil_moisture': data[1], 'temp': data[2] }, predictions))
    if len(predictions) > 0:
        return random.randint(0,1)
        # return predictions[0]
    return -1
