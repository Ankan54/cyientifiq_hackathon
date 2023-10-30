import json, os, requests, uuid
from dotenv import load_dotenv
load_dotenv()

def translate_text(input_text,lang):
    if len(input_text)<=0:
        return ''
        
    key= os.getenv('TRANSLATOR_KEY')
    endpoint = os.getenv('TEXT_TRANS_URL')
    location = os.getenv('COG_SERVICE_REGION')

    path = '/translate'
    constructed_url = endpoint + path

    lang_dict= {'hindi': 'hi', 'bengali': 'bn'}
    params = {'api-version': '3.0', 'from': lang_dict[lang], 'to': ['en']}

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        # location required if you're using a multi-service or regional (not global) resource.
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
        }

    body = [{'text': f'{input_text}'}]

    response = requests.post(constructed_url, params=params, headers=headers, json=body)
    response_json = response.json()

    if response.status_code != 200:
        print(json.dumps(response.json(), ensure_ascii=False, indent=4, separators=(',', ': ')))
        return False
    
    return response_json[0]['translations'][0]['text']