import requests
import json
import os
from requests.exceptions import Timeout, ConnectionError
from payload import bearer_token, api_url


# Create json folder if it doesn't exist
json_folder = "json"
if not os.path.exists(json_folder):
    os.makedirs(json_folder)

# Load mentors mapping
mentor_mapping = {}
mentors_file = os.path.join(json_folder, "mentors.json")
if os.path.exists(mentors_file):
    with open(mentors_file, 'r', encoding='utf-8') as f:
        mentors_data = json.load(f)
        for mentor in mentors_data.get('mentors', []):
            mentor_mapping[mentor['id']] = mentor['nama']
    print(f"Loaded {len(mentor_mapping)} mentors from mentors.json")
else:
    print(f"Warning: {mentors_file} not found")

# Initialize session for persistent login
session = requests.Session()

# Set Authorization header with Bearer token
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Authorization': f'Bearer {bearer_token}'
})

print("Authorization token set")
print("Login process completed")

# Initialize articles list and counter
articles_list = []
article_id_counter = 1
since_id = 0
next_id = 0

print("\n" + "="*60)
print("Starting to download articles...")
print("="*60 + "\n")

while True:
    try:
        # Build API URL with parameters
        params = {
            "sort": "desc",
            "since_id": since_id,
            "next_id": next_id,
            "mentor_ids": "",
            "categories": "",
            "year": "",
            "month": ""
        }
        
        print(f"Calling API with since_id={since_id}, next_id={next_id}...")
        
        # Make API call with 20 second timeout
        response = session.get(api_url, params=params, timeout=20)
        
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"DEBUG: Response data type: {type(data)}")
                print(f"DEBUG: Response data: {json.dumps(data, indent=2)[:500]}")
                
                # Check if data is empty or has no articles
                if not data or (isinstance(data, dict) and not data.get('data')) or (isinstance(data, list) and len(data) == 0):
                    print("[INFO] No more articles found. Scraping complete!")
                    break
                
                # Extract articles from response
                articles = data.get('data', data) if isinstance(data, dict) else data
                
                if not articles:
                    print("[INFO] No more articles found. Scraping complete!")
                    break
                
                # Process each article
                batch_count = 0
                for article in articles:
                    if isinstance(article, dict):
                        mentor_id = article.get("mentor_id", "")
                        mentor_name = mentor_mapping.get(mentor_id, "Unknown") if mentor_id else "Unknown"
                        # Remove newline characters from content
                        content = article.get("content", "").replace("\n", " ").replace("\r", "")
                        extracted_article = {
                            "id": article_id_counter,
                            "title": article.get("title", ""),
                            "content": content,
                            "mentor_name": mentor_name
                        }
                        articles_list.append(extracted_article)
                        batch_count += 1
                        article_id_counter += 1
                
                print(f"[+] Downloaded {batch_count} articles (Total: {len(articles_list)} articles)")
                
                # Update since_id for next call using last article's id
                if articles and isinstance(articles[-1], dict):
                    since_id = articles[-1].get("id", 0)
                    print(f"    Next since_id: {since_id}")
                
            except json.JSONDecodeError:
                print("[-] Failed to parse JSON response")
                break
        else:
            print(f"[-] API request failed: {response.status_code}")
            break
        
    except Timeout:
        print("[-] Request timeout - No response within 20 seconds. Stopping.")
        break
    except ConnectionError as e:
        print(f"[-] Connection error: {e}. Stopping.")
        break
    except Exception as e:
        print(f"[-] Unexpected error: {e}. Stopping.")
        break

# Save to JSONL file (JSON Lines format for LLM training)
output_path = os.path.join(json_folder, "articles.jsonl")
with open(output_path, 'w', encoding='utf-8') as f:
    for article in articles_list:
        f.write(json.dumps(article, ensure_ascii=False) + '\n')

print("\n" + "="*60)
print(f"[OK] Scraping complete!")
print(f"[OK] Total articles saved: {len(articles_list)}")
print(f"[OK] Saved to: {output_path} (JSONL format for LLM training)")
print("="*60)