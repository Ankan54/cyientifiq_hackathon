from flask import Flask, render_template
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
            r.call_timestamp, r.followup_required
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

if __name__ == '__main__':
    app.run(debug=True)