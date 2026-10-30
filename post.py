import requests
import csv
from itertools import islice


base_url = "http://206.187.214.111:8000/chat"

with open("/home/20261029/key.csv", "r") as f:
    reader = csv.reader(f)
    api_key = next(islice(reader, 0, 1), None)[1]

while True:
    user_input = input("请输入: ")
    if user_input.lower() == "exit":
        break
    user_message = {
        "model_name": "deepseek-flash",
        "api_key": api_key,
        "message": user_input,
        "session_id": "001"
    }
    response = requests.post(base_url, json=user_message)
    if response.status_code == 200:
        assistant_message = response.json().get("message")
        if response.json().get("reasoning"):
            reasoning_content = response.json().get("reasoning")
            print("thinking:", reasoning_content)
        print("response:", assistant_message)
    else:
        print("Error:", response.status_code, response.text)