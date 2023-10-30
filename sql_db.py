import sqlite3

def create_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    try:
        conn = sqlite3.connect('cyient_database.db')

        # Create a cursor object
        cursor = conn.cursor()

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print('Error Creating Database!! ',str(e))
        return False


def connect_database():
    try:
        conn = sqlite3.connect('cyient_database.db')
        return conn
    except Exception as e:
        print('Error connecting to Database!! ',str(e))
        return None


def create_tables():
    conn = connect_database()

    cursor = conn.cursor()

    create_table_call_details = '''
                                CREATE TABLE IF NOT EXISTS TBL_call_details(
                                    call_id TEXT NOT NULL PRIMARY KEY,
                                    caller_id TEXT NOT NULL,
                                    agent_id TEXT NOT NULL,
                                    audio_language TEXT NOT NULL,
                                    call_duration TEXT,
                                    time_on_hold INTEGER,
                                    time_overlapped INTEGER,
                                    duration_overlapped REAL,
                                    original_transcript TEXT,
                                    translated_transcript TEXT,
                                    transliterated_transcript TEXT,
                                    call_summary TEXT,
                                    followup_required INTEGER,
                                    overall_sentiment TEXT,
                                    positive_sentiment_score REAL,
                                    neutral_sentiment_score REAL,
                                    negative_sentiment_score REAL,
                                    keywords TEXT,
                                    category TEXT,
                                    call_timestamp TEXT NOT NULL,
                                    updation_timestamp TEXT NOT NULL,
                                    duration_on_hold REAL,
                                    hold_offsets TEXT
                                );
                                '''
    cursor.execute(create_table_call_details)

    create_table_call_phrases = '''
                                CREATE TABLE IF NOT EXISTS TBL_call_phrases(
                                    call_id TEXT NOT NULL,
                                    speaker INTEGER,
                                    phrase_start REAL,
                                    phrase_end REAL,
                                    phrase_duration REAL,
                                    overlapped INTEGER,
                                    overlap_duration REAL,
                                    original_phrase TEXT,
                                    translated_phrase TEXT,
                                    transliterated_phrase TEXT,
                                    updation_timestamp TEXT
                                );
                                '''
    cursor.execute(create_table_call_phrases)

    create_table_sentiment_phrases = '''
                                    CREATE TABLE IF NOT EXISTS TBL_sentiment_phrases(
                                        call_id TEXT NOT NULL,
                                        phrase_text TEXT,
                                        phrase_offset INTEGER,
                                        phrase_length INTEGER,
                                        phrase_sentiment TEXT,
                                        positive_sentiment_score REAL,
                                        neutral_sentiment_score REAL,
                                        negative_sentiment_score REAL,
                                        updation_timestamp TEXT
                                    );
                                    '''
    cursor.execute(create_table_sentiment_phrases)

    create_table_call_entities = '''
                                CREATE TABLE IF NOT EXISTS TBL_call_entities(
                                    call_id TEXT NOT NULL,
                                    entity_text TEXT,
                                    category TEXT,
                                    subcategory TEXT,
                                    offset INTEGER,
                                    length INTEGER,
                                    confidence_score REAL,
                                    updation_timestamp TEXT
                                );
                                '''
    cursor.execute(create_table_call_entities)

    create_table_agents = '''
                            CREATE TABLE IF NOT EXISTS TBL_raw_Agent(
                            Agent_id TEXT NOT NULL PRIMARY KEY,
                            Agent_Name TEXT
                        );
                        '''
    cursor.execute(create_table_agents)

    create_table_customers = '''
                            CREATE TABLE IF NOT EXISTS TBL_raw_customer(
                                caller_id TEXT NOT NULL PRIMARY KEY,
                                caller_name TEXT,
                                caller_age INTEGER,
                                caller_gender TEXT,
                                Location TEXT,
                                latitude REAL,
                                longitude REAL,
                                pincode TEXT
                            );
                            '''
    cursor.execute(create_table_customers)

    insert_customer_data = '''
                            INSERT INTO TBL_raw_customer (
                                caller_id,caller_name,caller_age,caller_gender,Location,latitude,longitude,pincode) 
                                VALUES
                                ('9876123454','Mr. X',30,'Female','Kolkata',22.572646,88.363895,'700012'),
                                ('8703764832','Mrs. A',35,'Male','Bangalore',12.972442,77.580643,'560004'),
                                ('9087636234','Mrs. R',27,'Male','Bangalore',12.972442,77.580643,'560030'),
                                ('9737564781','Mr. W',31,'Male','Bangalore',12.972442,77.580643,'560070'),
                                ('9876230198','Mr. Y',45,'Female','Bangalore',12.972442,77.580643,'560084'),
                                ('8981763467','Mr. Z',41,'Male','Delhi',28.652,77.2315,'110018'),
                                ('9403873954','Mr. M',28,'Female','Delhi',28.652,77.2315,'110054');
                            '''
    cursor.execute(insert_customer_data)

    insert_agent_data = '''
                        INSERT INTO TBL_raw_Agent (
                        Agent_id,Agent_Name)
                        VALUES
                        ('A1','Agent 1'),
                        ('A2','Agent 2'),
                        ('A3','Agent 3')
                        '''
    cursor.execute(insert_agent_data)

    conn.commit()
    conn.close()



#connect_database()
#create_tables()