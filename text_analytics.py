from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
import pandas as pd
from datetime import datetime
from sql_db import connect_database
import os
from dotenv import load_dotenv
load_dotenv()


def extract_sentiments(call_data):
    credential = AzureKeyCredential(f"{os.getenv('COG_SERVICE_KEY')}")
    text_analytics_client = TextAnalyticsClient(endpoint=f"{os.getenv('COG_SERVICE_ENDPOINT')}", credential=credential)

    list_overall_dict=[]
    list_sent_dict=[]
    for call in call_data:
        documents = [
            {"id": call[0], "language": "en", "text": call[1]},
        ]
        print('extracting sentiments:',call[0])
        result = text_analytics_client.analyze_sentiment(documents, show_opinion_mining=True)
        docs = [doc for doc in result if not doc.is_error]
        if len(docs)<=0:
            print('Error: No successful response')
            return False

        for _, doc in enumerate(docs):
            temp_overall_dict= {}
            temp_overall_dict['call_id']= doc.id
            temp_overall_dict['overall_sentiment']= doc.sentiment
            temp_overall_dict['positive_sentiment']= doc.confidence_scores.positive
            temp_overall_dict['neutral_sentiment']= doc.confidence_scores.neutral
            temp_overall_dict['negative_sentiment']= doc.confidence_scores.negative
            list_overall_dict.append(temp_overall_dict)

            for sentence in doc.sentences:
                temp_sent_dict= {}
                temp_sent_dict['call_id']= doc.id
                temp_sent_dict['sentence']= sentence.text
                temp_sent_dict['sentence_offset']= sentence.offset
                temp_sent_dict['sentence_length']= sentence.length
                temp_sent_dict['overall_sentiment']= sentence.sentiment
                temp_sent_dict['positive_sentiment']= sentence.confidence_scores.positive
                temp_sent_dict['neutral_sentiment']= sentence.confidence_scores.neutral
                temp_sent_dict['negative_sentiment']= sentence.confidence_scores.negative
                list_sent_dict.append(temp_sent_dict)

    if len(list_overall_dict)<=0:
        print('Error: no result returned')
        return False
        
    overall_df= pd.DataFrame(list_overall_dict)
    sentence_df= pd.DataFrame(list_sent_dict)

    conn= connect_database()
    cursor= conn.cursor()
    print('updating overall sentiments....')
    for _, row in overall_df.iterrows():
        query= f''' INSERT INTO TBL_call_details (
                        call_id, overall_sentiment, positive_sentiment_score,
                        neutral_sentiment_score, negative_sentiment_score, updation_timestamp)
                    VALUES (
                        '{row['call_id']}', N'{row['overall_sentiment']}', {row['positive_sentiment']},
                        {row['neutral_sentiment']}, {row['negative_sentiment']},
                        '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}'
                    )
                    ON CONFLICT(call_id) DO UPDATE SET
                        overall_sentiment = '{row['overall_sentiment']}',
                        positive_sentiment_score = {row['positive_sentiment']},
                        neutral_sentiment_score = {row['neutral_sentiment']},
                        negative_sentiment_score = {row['negative_sentiment']},
                        updation_timestamp = '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}';
                '''
        try:
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            print(query)
            conn.close()
            print(str(e))
            return False
    
    print('updating sentence sentiments....')
    for _, row in sentence_df.iterrows():
        query= f''' INSERT INTO TBL_sentiment_phrases (
                        call_id, phrase_offset, phrase_text, phrase_length,
                        phrase_sentiment, positive_sentiment_score,
                        neutral_sentiment_score, negative_sentiment_score, updation_timestamp)
                    VALUES (
                        '{row['call_id']}', {row['sentence_offset']}, '{row['sentence'].replace("'","''")}', {row['sentence_length']},
                        '{row['overall_sentiment']}', '{row['positive_sentiment']}',
                        '{row['neutral_sentiment']}', '{row['negative_sentiment']}',
                        '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}'
                    )
                    ON CONFLICT(call_id) DO UPDATE SET
                        phrase_offset = {row['sentence_offset']},
                        phrase_text = '{row['sentence'].replace("'","''")}',
                        phrase_length = {row['sentence_length']},
                        phrase_sentiment = '{row['overall_sentiment']}',
                        positive_sentiment_score = {row['positive_sentiment']},
                        negative_sentiment_score = {row['negative_sentiment']},
                        neutral_sentiment_score = {row['neutral_sentiment']},
                        updation_timestamp = '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}';
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


def extract_entities(call_data):
    credential = AzureKeyCredential(f"{os.getenv('COG_SERVICE_KEY')}")
    text_analytics_client = TextAnalyticsClient(endpoint=f"{os.getenv('COG_SERVICE_ENDPOINT')}", credential=credential)

    list_key_dict=[]
    for call in call_data:
        print('extracting entities:',call[0])
        articles = [
            {"id": call[0], "language": "en", "text": call[1]},
        ]

        result = text_analytics_client.recognize_entities(articles)
        for _, doc in enumerate(result):
            if doc.is_error:
                continue
            call_id = doc.id
            for entity in doc.entities:
                temp_key_dict={}
                temp_key_dict['call_id']= call_id
                temp_key_dict['entity_text']= entity.text
                temp_key_dict['category']= entity.category
                temp_key_dict['offset']= entity.offset
                temp_key_dict['length']= entity.length
                temp_key_dict['subcategory']= entity.subcategory
                temp_key_dict['confidence_score']= entity.confidence_score
                list_key_dict.append(temp_key_dict)
        
    if len(list_key_dict)<=0:
        print('Error: no entity returned')
        return True

    entity_df= pd.DataFrame(list_key_dict)
    entity_df= entity_df.fillna('')
    conn= connect_database()
    cursor= conn.cursor()
    print('updating entities...')
    for _, row in entity_df.iterrows():
        query= f''' INSERT INTO TBL_call_entities (
                        call_id, entity_text, category, subcategory,
                        offset, length, confidence_score,
                        updation_timestamp)
                    VALUES (
                        '{row['call_id']}', '{row['entity_text'].replace("'","''")}',
                        '{row['category'].replace("'","''")}', '{row['subcategory'].replace("'","''")}',
                        {row['offset']}, {row['length']}, {row['confidence_score']},
                        '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}'
                    )
                    ON CONFLICT(call_id) DO UPDATE SET
                        entity_text = '{row['entity_text'].replace("'","''")}',
                        category = '{row['category'].replace("'","''")}',
                        subcategory = '{row['subcategory'].replace("'","''")}',
                        offset = {row['offset']},
                        length = {row['length']},
                        confidence_score = {row['confidence_score']},
                        updation_timestamp = '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}';
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


def text_analytics_main(call_id_list):

    for call_id in call_id_list:
        conn= connect_database()
        cursor= conn.cursor()
        call_data= cursor.execute(f"select [call_id],[translated_transcript] from [dbo].[TBL_call_details] where call_id = '{call_id}'").fetchall()
        conn.close()

        if not extract_sentiments(call_data):
            print('Error extracting sentiments')
            return False

        if not extract_entities(call_data):
            print('Error extracting entities')
            return False
    
    return True