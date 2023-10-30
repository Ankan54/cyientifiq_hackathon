import numpy as np
import pandas as pd
import librosa,os
from sql_db import connect_database
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()


def find_silence(filename):
    print('processing:', filename)
    y, sr = librosa.load(filename, sr=44100, mono=False)
    y_8k = librosa.resample(y, orig_sr=sr, target_sr=8000)
    y_8k_mono = librosa.to_mono(y_8k)

    dur = np.arange(0, len(y_8k_mono)) / 8000

    call_id = filename.split('.')[0].split('\\')[-1]
    call_time = call_id.split('_')[3:]
    temp_dict= {'call_id': call_id,
                'caller_id': call_id.split('_')[1], 'agent_id': call_id.split('_')[2],
                'call_timestamp': datetime.strptime(call_time[0] +' '+ call_time[1], '%y%m%d %H%M%S').strftime("%d-%m-%y %H:%M:%S"),
                'audio_language': call_id.split('_')[0], 'hold_time': [], 'duration': 0.0}
    start = -1
    end = -1
    prev_flag = 0 #no silence
    for i in range(len(dur)):
        lst_time= []
        if y_8k_mono[i]<0.2 and start == -1:
            start = dur[i]
            prev_flag = 1
        if y_8k_mono[i]>=0.2 and start != -1:
            end = dur[i-1]
            if end-start > 5: # silence more than 5 seconds
            #print("started at ", start, " and ended at ", end)
                tpl_time= (start,end)
                temp_dict['hold_time'].append(tpl_time)
                temp_dict['duration']= temp_dict['duration']+ (end-start)
            start = -1
            end = -1
    
    temp_dict['count']= len(temp_dict['hold_time'])
    #print(temp_dict)
    return temp_dict


def audio_processing_main(path):
    dir_list = os.listdir(path)
    lst_hold= []
    for filename in dir_list:
        lst_hold.append(find_silence(os.path.join(path,filename)))

    if len(lst_hold)<=0:
        print('No file to process.')
        return False

    df= pd.DataFrame(lst_hold)

    conn= connect_database()
    cursor= conn.cursor()

    for _, row in df.iterrows():
        #print(row)
        query= f'''INSERT INTO TBL_call_details (
                    call_id,caller_id, agent_id, audio_language, time_on_hold, duration_on_hold, hold_offsets,call_timestamp, updation_timestamp)
                VALUES (
                    '{row['call_id']}','{row['caller_id']}','{row['agent_id']}',
                    '{row['audio_language']}',{row['count']}, {row['duration']}, '{row['hold_time']}',
                    '{row['call_timestamp']}','{datetime.now().strftime("%d-%m-%y %H:%M:%S")}')
                ON CONFLICT(call_id) DO UPDATE SET
                    caller_id = '{row['caller_id']}',
                    agent_id = '{row['agent_id']}',
                    audio_language = '{row['audio_language']}',
                    time_on_hold = {row['count']},
                    duration_on_hold = {row['duration']},
                    hold_offsets = '{row['hold_time']}',
                    call_timestamp = '{row['call_timestamp']}',
                    updation_timestamp = '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}';'''
        try:
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            #print(query)
            print(str(e))
            conn.close()
            return False
    
    conn.close()
    print('done!')
    return True


if __name__ == "__main__":
    #local_path = r"F:\Cyient_Hackathon\recordings\processed"
    local_path = r"{}".format(os.getenv('COG_SERVICE_REGION'))
    if not audio_processing_main(local_path):
        print('Error: Process Failed!')