
import json
import os

file_path = 'daily_gainers_history.json'

if not os.path.exists(file_path):
    print("File not found.")
else:
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        dates_to_check = ['01-01', '01-02', '01-03', '01-04']
        found = []
        missing = []
        
        for date in dates_to_check:
            if date in data:
                found.append(date)
            else:
                missing.append(date)
                
        print(f"Total dates in file: {len(data.keys())}")
        print(f"Dates found: {found}")
        print(f"Dates missing: {missing}")
        
    except Exception as e:
        print(f"Error reading file: {e}")
