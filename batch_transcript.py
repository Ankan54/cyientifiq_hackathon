import os,requests
import json, time
from dotenv import load_dotenv
load_dotenv()


def batch_transcript(src_container_sas,dest_container_sas,lang):
  url= "https://{}.api.cognitive.microsoft.com/speechtotext/v3.0/transcriptions/".format(os.getenv('COG_SERVICE_REGION'))

  headers = {"Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": os.getenv('SPEECH_TO_TEXT_KEY')}

  locale_dict= {'hindi': 'hi-IN', 'bengali': 'bn-IN', 'english': 'en-IN'}

  if lang not in locale_dict.keys():
    print('Error: Invalid language!')
    return False
  
  json_data = {
      "contentContainerUrl": src_container_sas,
      "properties": {
        "diarizationEnabled": "true",
        "wordLevelTimestampsEnabled": "false",
        "punctuationMode": "DictatedAndAutomatic",
        "profanityFilterMode": "Masked",
        "destinationContainerUrl": dest_container_sas 
      },
      "locale": locale_dict[lang],
      "displayName": f"transcripting {lang} audio files from {lang}-audio-raw and storing them in {lang}-audio-processed"
    }
  
  response = requests.post(url, headers=headers, json=json_data)
  response_json=response.json()
  print('Status:', response.status_code)
  if response.status_code != 201:
    print(json.dumps(response_json, ensure_ascii=False, indent=4, separators=(',', ': ')))
    return False
  
  status=''
  while status != 'Succeeded':
    print(response_json['self']) #debug line
    check_status_url= response_json['self']
    print('checking status in 10 seconds...')
    time.sleep(10)
    check_status_response = requests.get(check_status_url, headers=headers)
    if check_status_response.status_code == 200:
      status= check_status_response.json()['status']
      print('Status:', status)
    else:
      print(json.dumps(check_status_response.json(), ensure_ascii=False, indent=4, separators=(',', ': ')))
      return False
  
  return check_status_url.split('/')[-1]
