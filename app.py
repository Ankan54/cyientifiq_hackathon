from flask import Flask, render_template, request, jsonify
import pandas as pd
import sqlite3

app = Flask(__name__)


def get_agents():
    conn = sqlite3.connect('cyient_database.db') 
    cursor = conn.cursor()
    cursor.execute('SELECT agent_id, agent_name FROM TBL_raw_Agent')
    agents = cursor.fetchall()
    conn.close()

    return agents

def get_call_records():
    query = '''select r.call_id, r.caller_id,
            a.agent_name, r.audio_language,
            printf("%02d:%02d:%02d", r.call_duration / 3600, (r.call_duration % 3600) / 60, r.call_duration % 60) as call_duration,
            r.call_timestamp, r.followup_required, r.keywords
            FROM TBL_call_details r 
            INNER JOIN TBL_raw_Agent a on r.agent_id = a.agent_id;'''
    conn = sqlite3.connect('cyient_database.db') 
    cursor = conn.cursor()
    cursor.execute(query)
    call_records = cursor.fetchall()
    conn.close()

    return call_records

@app.route('/')
def index():
    agents= get_agents()
    call_records = get_call_records()
    return render_template('index.html', agents=agents,call_records=call_records)

@app.route('/filter_records', methods=['POST'])
def filter_records():
    data = request.get_json()
    date_from = data.get('date_from')
    date_to = data.get('date_to')
    language = data.get('language')
    agent = data.get('agent')
    keywords = data.get('keywords')

    print(data)

    sql_query = """
                SELECT r.call_id, r.caller_id, a.agent_name, r.audio_language,
                    printf("%02d:%02d:%02d", r.call_duration / 3600, (r.call_duration % 3600) / 60, r.call_duration % 60) as call_duration,
                    r.call_timestamp, r.followup_required, r.keywords, r.agent_id
                FROM TBL_call_details r 
                INNER JOIN TBL_raw_Agent a ON r.agent_id = a.agent_id;
                """
    conn = sqlite3.connect('cyient_database.db') 
    df_call_records = pd.read_sql_query(sql_query,conn)
    conn.close()

    df_call_records['call_date'] = pd.to_datetime(df_call_records['call_timestamp'],format='%d-%m-%y %H:%M:%S').dt.date
    df_call_records['keywords_list'] = df_call_records['keywords'].apply(lambda x: set(x.split(',')))

    if date_from:
        date_from = pd.to_datetime(date_from)
        df_call_records = df_call_records[df_call_records['call_date']>=date_from]
    
    if date_to:
        date_to = pd.to_datetime(date_to)
        df_call_records = df_call_records[df_call_records['call_date']<=date_to]

    if language and language != 'all':
        df_call_records = df_call_records[df_call_records['audio_language']== language]

    if agent and agent != 'all':
        df_call_records = df_call_records[df_call_records['agent_id']== agent]

    if keywords:
        keywords = set(keywords.split(','))
        df_call_records = df_call_records[df_call_records['keywords_list'].apply(lambda x: any(any(word.lower() in phrase.lower().split() for word in keywords) for phrase in x))]
    
    df_filtered = df_call_records[['call_id','caller_id','Agent_Name','audio_language','call_duration','call_timestamp','followup_required']]
    filtered_records = list(df_filtered.to_dict(orient='records'))

    return jsonify({
        "message": "Filtering successful",
        "criteria": data,
        'filtered_data': filtered_records
    })

if __name__ == '__main__':
    app.run(debug=True)