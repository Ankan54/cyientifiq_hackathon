from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
from datetime import datetime
import pandas as pd
import os, json, shutil, random
from translate_text import translate_text
from transliterate_text import transliterate_text
from parse_transcript_phrases import process_audio_time, parse_phrases
# from text_analytics import text_analytics_main
from sql_db import connect_database
from dotenv import load_dotenv
load_dotenv()


def parse_transcript(uid,lang):
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={os.getenv('BLOB_STORAGE_NAME')};AccountKey={os.getenv('BLOB_STORAGE_KEY')};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    container_name = f'{lang}-audio-processed'
    container_client=  blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs(name_starts_with=f'{uid}/{lang}-audio-raw/')

    trans_dict_list= []
    for blob in blob_list:
        file_path= os.path.join(os.getcwd(),'transcript_json')
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        download_file_path= os.path.join(file_path, 'temp.json')
        with open(download_file_path, "wb") as download_file:
            download_file.write(container_client.download_blob(blob.name).readall())

        text_data=''
        json_dict= None
        with open(download_file_path, "r", encoding='utf-8') as json_file:
            json_dict = json.load(json_file)
            text_data = (json_dict['combinedRecognizedPhrases'][0]['display'])
        
        shutil.rmtree(download_file_path, ignore_errors=True) # remove json file

        trans_text=''
        translit_text=''
        print('translating {} ....'.format(blob.name.split('/')[-1]))
        if lang != 'english':
            trans_text= translate_text(text_data,lang)
            if trans_text == False:
                print('Error while translating.')
                return False
            translit_text= transliterate_text(text_data,lang)
            if translit_text == False:
                print('Error while transliterating.')
                return False
        else:
            text_data= text_data.replace("'","''")
            trans_text= text_data
            translit_text= text_data

        filename= blob.name
        call_id =  filename.split('/')[-1].split('.')[0]
        call_time= call_id.split('_')[3:]
        trans_dict= {'call_id': call_id,
                    'caller_id': call_id.split('_')[1], 'agent_id': call_id.split('_')[2],
                    'call_timestamp': datetime.strptime(call_time[0] +' '+ call_time[1], '%y%m%d %H%M%S').strftime("%d-%m-%y %H:%M:%S"),
                    'original_transcript': text_data,
                    'translated_transcript': trans_text.replace("'","''"),
                    'transliterated_transcript': translit_text.replace("'","''"),
                    'duration': json_dict['duration']}

        trans_dict_list.append(trans_dict)

    if len(trans_dict_list)>0:
        trans_dict_df = pd.DataFrame(trans_dict_list)
        trans_dict_df['duration_in_sec']= trans_dict_df['duration'].apply(lambda x: process_audio_time(x))
        
        print('updating call_details table...')
        conn= connect_database()
        cursor= conn.cursor()

        for _, row in trans_dict_df.iterrows():
            query= f''' INSERT INTO TBL_call_details (
                            call_id, caller_id, Agent_id, audio_language, call_duration, original_transcript,
                            translated_transcript, transliterated_transcript, call_timestamp, updation_timestamp)
                        VALUES (
                            '{row['call_id']}', '{row['caller_id']}', '{row['agent_id']}', '{lang}', '{row['duration_in_sec']}',
                            '{row['original_transcript']}', '{row['translated_transcript'].replace("'","''")}', '{row['transliterated_transcript'].replace("'","''")}',
                            '{row['call_timestamp']}', '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}'
                        )
                        ON CONFLICT(call_id) DO UPDATE SET
                            caller_id = '{row['caller_id']}',
                            Agent_id = '{row['agent_id']}',
                            audio_language = '{lang}',
                            call_duration = '{row['duration_in_sec']}',
                            original_transcript = '{row['original_transcript']}',
                            translated_transcript = '{row['translated_transcript'].replace("'","''")}',
                            transliterated_transcript = '{row['transliterated_transcript'].replace("'","''")}',
                            call_timestamp = '{row['call_timestamp']}',
                            updation_timestamp = '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}';'''
            try:
                cursor.execute(query)
                conn.commit()
            except Exception as e:
                print(query)
                conn.close()
                print(str(e))
                return False
        conn.close()