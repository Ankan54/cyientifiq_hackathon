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

@app.route('/')
def index():
    agents= get_agents()
    return render_template('index.html', agents=agents)

if __name__ == '__main__':
    app.run(debug=True)