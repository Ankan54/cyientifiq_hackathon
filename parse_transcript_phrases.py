from datetime import datetime
import pandas as pd
from sql_db import connect_database
from translate_text import translate_text
from transliterate_text import transliterate_text


def process_audio_time(input):
    output= input[2:-1]
    if 'M' in input:
        output= float(output.split('M')[0]) * 60 + float(output.split('M')[1])
    return output


def parse_phrases(phrase_list,filename,lang):
    list_dict= []
    for phrase in phrase_list:
        temp_dict= {}
        if phrase['recognitionStatus'] != 'Success':
            continue
        channel= phrase['channel']
        speaker= phrase['speaker']
        offset= phrase['offset']
        duration= phrase['duration']
        nBest= phrase['nBest'][0]
        confidence= nBest['confidence']
        text= nBest['lexical']

        temp_dict= {
            'channel': channel,
            'speaker': speaker,
            'offset': offset,
            "duration": duration,
            "confidence": confidence,
            'text': text
        }
        list_dict.append(temp_dict)

    if len(list_dict)<=0:
        print('no phrases to extract')
        return True
    
    phrases_df= pd.DataFrame(list_dict)
    phrases_df['start_sec'] = phrases_df['offset'].apply(lambda x: process_audio_time(x)).astype(float)
    phrases_df['duration_in_sec']= phrases_df['duration'].apply(lambda x: process_audio_time(x)).astype(float)
    phrases_df.drop(columns=['offset','duration'],axis=1, inplace=True)
    phrases_df['end_sec'] = phrases_df['start_sec'] + phrases_df['duration_in_sec'].astype(float)
    phrases_df['prev_speaker_end_sec'] = phrases_df['end_sec'].shift(1).fillna(-1)
    phrases_df.loc[phrases_df['prev_speaker_end_sec']>phrases_df['start_sec'],'mark_cross_talk'] = 1
    phrases_df['mark_cross_talk'] = phrases_df['mark_cross_talk'].fillna(0)

    first_speaker = phrases_df.iloc[0]['speaker'] 
    phrases_df.loc[(((phrases_df['mark_cross_talk']>0)&(phrases_df['speaker']==first_speaker))==True),'Agent_crossed_Customer'] = 1
    phrases_df['Agent_crossed_Customer'] = phrases_df['Agent_crossed_Customer'].fillna(0) 
    phrases_df['Agent_crossed_Customer']= phrases_df['Agent_crossed_Customer'].astype(int) # this is the overlapped boolean column
    phrases_df['cross_talk_duration'] = phrases_df['prev_speaker_end_sec'] - phrases_df['start_sec']
    phrases_df.loc[phrases_df['cross_talk_duration']<0, 'cross_talk_duration'] =0

    phrases_df['call_id']= filename.split('/')[-1].split('.')[0]
    if lang != 'english': 
        phrases_df['translated_text']= phrases_df['text'].apply(lambda x: translate_text(x,lang) if lang!='english' else x)
        phrases_df['transliterated_text']= phrases_df['text'].apply(lambda x: transliterate_text(x,lang) if lang!='english' else x)
    else:
        phrases_df['text']= phrases_df['text'].apply(lambda x: x.replace("'","''"))
        phrases_df['translated_text'] = phrases_df['text']
        phrases_df['transliterated_text'] = phrases_df['text']

    conn= connect_database()
    cursor= conn.cursor()

    for _, row in phrases_df.iterrows():
        query = f'''
                INSERT INTO TBL_call_phrases (
                    call_id, speaker, phrase_start, phrase_end, overlapped, phrase_duration, overlap_duration,
                    original_phrase, translated_phrase, transliterated_phrase, updation_timestamp)
                VALUES (
                    '{row['call_id']}', '{row['speaker']}', {row['start_sec']}, {row['end_sec']}, {row['Agent_crossed_Customer']},
                    {row['duration_in_sec']}, {row['cross_talk_duration']}, '{row['text']}', 
                    '{row['translated_text'].replace("'","''")}', '{row['transliterated_text'].replace("'","''")}',
                    '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}'
                );
                '''
        try:
            cursor.execute(query)
            conn.commit()

        except Exception as e:
            print(query)
            conn.close()
            print(str(e))
            return False
    
    conn.close()
    return True