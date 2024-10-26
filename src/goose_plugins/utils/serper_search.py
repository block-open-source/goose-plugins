import os
import json
import requests

def serper_search(query: str) -> str:
  payload = json.dumps({ 'q': query })
  headers = {
    'X-API-KEY': os.getenv('SERPER_API_KEY'),
    'Content-Type': 'application/json'
  }
  response = requests.request(
      'POST',
      'https://google.serper.dev/search',
      headers=headers, data=payload
  )
  return response.text
