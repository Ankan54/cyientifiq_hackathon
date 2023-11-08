from flask import Flask, render_template, request, jsonify
import pandas as pd
import sqlite3, openai, os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
openai.api_key = os.getenv('OPENAI_API_KEY')

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


@app.route('/generate_resource', methods=['POST'])
def generate_resource():
    data = request.get_json()
    topic = data.get('topic')
    word_limit = data.get('word_limit')
    temperature = data.get('temperature')
    remarks = data.get('remarks')
    call_id = data.get('call_id')

    prompt_template = '''
                        Role: You are a AI assistant with expertise in credit card sales.
                        Job Description: You have been provided the transcript of a sales call between a customer and sales agent regarding credit card sales.
                        You also have been provided with the customer details, their BANT analysis and overall sentiment of the call. 
                        You need to write personalised text on the topic as mentioned below within the given word limit.

                        Topic: {topic_name}
                        Customer Name: {cust_name}
                        Customer Age: {cust_age}
                        Customer Gender: {cust_gender}
                        Customer Location: {cust_location}

                        Call Transcript: {call_transcript}
                        Call Duration in Second: {call_duration}
                        Call Sentiment: {call_sentiment}

                        Customer Budget: {cust_budget}
                        Customer Authority: {cust_authority}
                        Customer Need: {cust_need}
                        Customer Timeline: {cust_timing}
                        
                        Additional Information: {remarks}

                        Word Limit: {word_limit}

                        Answer:
                    '''
    
    call_details_query = f'''
                         select r.call_id, r.caller_id,c.caller_name, c.Location, c.caller_age, c.caller_gender, r.call_duration,
                         r.budget, r.need, r.authority, r.timing, r.overall_sentiment, r.translated_transcript
                         FROM TBL_call_details r inner JOIN TBL_raw_customer c on r.caller_id = c.caller_id 
                         where call_id = '{call_id}';
                         '''
    conn = sqlite3.connect('cyient_database.db') 
    cursor = conn.cursor()
    result = cursor.execute(call_details_query).fetchall()
    conn.close()

    prompt = prompt_template.format(topic_name= topic,
                                    cust_name= result[0][2],
                                    cust_age= result[0][4],
                                    cust_gender= result[0][5], 
                                    cust_location= result[0][3],
                                    call_transcript= result[0][12],
                                    call_duration= result[0][6],
                                    call_sentiment=result[0][11],
                                    cust_budget= result[0][7],
                                    cust_authority= result[0][9],
                                    cust_need= result[0][8],
                                    cust_timing= result[0][10],
                                    remarks= remarks if remarks else 'Not Mentioned',
                                    word_limit=word_limit)

    response = openai.Completion.create(model="text-davinci-003",
                                        prompt= prompt,
                                        temperature= float(temperature),
                                        max_tokens=2000,
                                        top_p=1,
                                        frequency_penalty=0,
                                        presence_penalty=0)

    output = response['choices'][0]['text']

    return jsonify({
        "message": "Generated {}".format(topic),
        "output": output
    })


@app.route('/call_details/<string:call_id>')
def call_details(call_id):
    print('call_id', call_id)
    call_details_query = f"""
                SELECT r.call_id, r.caller_id, c.caller_name,c.caller_age, c.caller_gender, c.Location, a.agent_name, r.audio_language,
                    printf("%02d:%02d:%02d", r.call_duration / 3600, (r.call_duration % 3600) / 60, r.call_duration % 60) as call_duration,
                    r.call_timestamp, r.followup_required, r.agent_id, r.call_summary, r.keywords, r.audio_path,
                    r.budget, r.authority, r.need, r.timing
                FROM TBL_call_details r 
                INNER JOIN TBL_raw_Agent a ON r.agent_id = a.agent_id
				INNER JOIN TBL_raw_customer c ON c.caller_id = r.caller_id
				where call_id = '{call_id}';
                """
    
    call_phrases_query = f'''
                        SELECT phrase_start,
                        printf("%02d:%02d:%02d", phrase_start / 3600, (phrase_start % 3600) / 60, phrase_start % 60) as timestamp,
                        translated_phrase FROM TBL_call_phrases 
                        where call_id = '{call_id}' ORDER BY phrase_start;
                        '''
    
    keywords_query = f'''
                        SELECT keywords from TBL_call_details where call_id = '{call_id}';
                      '''
    
    action_items_query = f'''
                            SELECT action_items from TBL_call_details where call_id = '{call_id}';
                          '''


    conn = sqlite3.connect('cyient_database.db') 
    df_call_details = pd.read_sql_query(call_details_query,conn)
    df_call_phrases = pd.read_sql_query(call_phrases_query,conn)
    df_keywords = pd.read_sql_query(keywords_query,conn)
    df_action_items = pd.read_sql_query(action_items_query,conn)
    conn.close()

    call_details = list(df_call_details.to_dict(orient='records'))

    call_phrases = list(df_call_phrases.to_dict(orient='records'))

    df_keywords['keywords_list'] = df_keywords['keywords'].apply(lambda x: set(x.split(',')))
    keywords_list = list(df_keywords['keywords_list'].values[0])

    df_action_items['items_list'] = df_action_items['action_items'].apply(lambda x: set(x.split(',')))
    action_items_list = list(df_action_items['items_list'].values[0])

    return render_template('call_details.html', call_details=call_details,
                           call_phrases=call_phrases, keywords_list=keywords_list, action_items_list=action_items_list)




if __name__ == '__main__':
    app.run(debug=True)