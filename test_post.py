import requests
import json
import time

try:
    print("Loading model...")
    res_m = requests.post("http://127.0.0.1:7070/api/load-model", json={"model_key":"kronos-mini", "device":"cpu"})
    
    time.sleep(1)
    print("\nSending prediction request with sample_count=5...")
    res_p = requests.post("http://127.0.0.1:7070/api/predict", json={
        "symbol": "BBOB",
        "lookback": 300,
        "pred_len": 10,
        "start_date": "2024-04-14T00:00:00",
        "sample_count": 5
    })
    
    if res_p.status_code == 200:
        data = res_p.json()
        print("Prediction Keys:", data.keys())
        print("First Prediction Result object:", data['prediction_results'][0])
    else:
        print("Error:", res_p.status_code, res_p.text)
except Exception as e:
    print("Exception during test:", e)
