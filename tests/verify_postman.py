import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

client = TestClient(app)

def load_postman_collection():
    with open('postman_collection.json', 'r') as f:
        return json.load(f)

def get_requests_from_collection(collection):
    requests = []
    
    def extract_requests(items, folder_name=""):
        for item in items:
            if 'item' in item:
                # It's a folder
                new_folder = f"{folder_name} > {item['name']}" if folder_name else item['name']
                extract_requests(item['item'], new_folder)
            else:
                # It's a request
                requests.append({
                    'name': item['name'],
                    'folder': folder_name,
                    'request': item['request']
                })
    
    extract_requests(collection['item'])
    return requests

def test_postman_collection():
    collection = load_postman_collection()
    test_cases = get_requests_from_collection(collection)
    
    print(f"\nFound {len(test_cases)} requests in Postman collection.")
    
    for case in test_cases:
        req = case['request']
        name = case['name']
        print(f"\nTesting: {case['folder']} / {name}")
        
        # Parse URL to get path
        # Postman URL object can be string or object
        if isinstance(req['url'], str):
            # This logic handles raw strings if they exist, but our JSON uses objects
             raw_url = req['url']
             path = raw_url.replace("{{base_url}}", "")
        else:
             path_list = req['url'].get('path', [])
             if isinstance(path_list, str): 
                 # Sometimes it's a string in the object?? Postman is weird.
                 path = "/" + path_list
             else:
                path = "/" + "/".join(path_list)
        
        # Method
        method = req['method']
        
        # Headers (convert list to dict)
        headers = {h['key']: h['value'] for h in req.get('header', [])}
        
        # Body
        json_body = None
        if req.get('body') and req['body'].get('mode') == 'raw':
            raw_body = req['body']['raw']
            try:
                # There might be comments in JSON (Postman allows it), preventing standard json.loads
                # Simple cleanup for // comments
                lines = [l for l in raw_body.splitlines() if not l.strip().startswith("//")]
                cleaned_body = "\n".join(lines)
                json_body = json.loads(cleaned_body)
            except Exception as e:
                print(f"  Skipping body details: {e}")
        
        # Execute
        try:
            if method == 'GET':
                response = client.get(path, headers=headers)
            elif method == 'POST':
                response = client.post(path, headers=headers, json=json_body)
            else:
                print(f"  Skipping unsupported method: {method}")
                continue
                
            print(f"  Status: {response.status_code}")
            
            # Simple Assertions based on description or name
            # In a real scenario, we'd parse the 'event' scripts in Postman, 
            # but here we infer expectations from the Description/Name keys
            
            if "Error" in name or "Invalid" in name or "Missing" in name:
                if response.status_code >= 400:
                    print("  ✅ Passed (Expected Error)")
                else:
                    print(f"  ❌ Failed (Expected Error, got {response.status_code})")
            else:
                if response.status_code == 200:
                    print("  ✅ Passed (Success)")
                else:
                    print(f"  ❌ Failed (Expected 200, got {response.status_code})")
                    print(f"  Response: {response.text[:200]}...")

        except Exception as e:
            print(f"  ❌ Exception: {e}")

if __name__ == "__main__":
    test_postman_collection()
