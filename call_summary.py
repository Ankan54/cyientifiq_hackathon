from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
import openai, os
import pandas as pd
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field
from sql_db import connect_database
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.environ['OPENAI_API_KEY']

model = ChatOpenAI(temperature=0,model="gpt-3.5-turbo-16k")

class Call_Details(BaseModel):
    """Information from the transcript"""
    summary: str = Field(description="Provide a concise summary of the transcript within 200 words.")
    followup_required: str = Field(description="Write 'Yes' if the customer wants the agent to followup or if the conversation implies a need to followup, otherwise write 'No'", enum=["Yes","No"])
    action_items: List = Field(description="Provide a list of action items from the transcript (atleast one) as applicable for the agent.")
    keywords: List = Field(description="Provide a list of keywords related to Banking and credit card sales from the transcript.")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Provided is the transcript of a credit card sales call between a customer and an agent. Think carefully, and then generate response as instructed"),
    ("human", "{input}")
])

overview_tagging_function = [
    convert_pydantic_to_openai_function(Call_Details)
]
tagging_model = model.bind(
    functions=overview_tagging_function,
    function_call={"name":"Call_Details"}
)
tagging_chain = prompt | tagging_model | JsonOutputFunctionsParser()


def get_call_summary(call_data):
    summary_dict_list= []
    for call in call_data:
        try:
            summary_dict = {'call_id': call[0]}
            transcript = call[1]
            call_summary_dict = tagging_chain.invoke({"input":f"{transcript}"})

            summary_dict['call_summary']= call_summary_dict['summary']
            summary_dict['followup_required']= call_summary_dict['followup_required']
            summary_dict['action_items']= ','.join(call_summary_dict['action_items'])
            summary_dict['keywords']= ','.join(call_summary_dict['keywords'])

            summary_dict_list.append(summary_dict)
        
        except Exception as e:
            print('call_id',call[0])
            print('Error:',str(e))
            continue

    print("updating call summary...")

    summary_df= pd.DataFrame(summary_dict_list)
    conn= connect_database()
    cursor= conn.cursor()

    for _, row in summary_df.iterrows():
        query = f'''
                UPDATE TBL_call_details
                SET call_summary = '{row['call_summary'].replace("'","''")}',
                    followup_required = '{row['followup_required']}',
                    action_items = '{row['action_items'].replace("'","''")}',
                    keywords = '{row['keywords'].replace("'","''")}',
                    updation_timestamp = '{datetime.now().strftime("%d-%m-%y %H:%M:%S")}'
                WHERE call_id = '{row['call_id']}';
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


def call_summary_main(call_id_list):
    for call_id in call_id_list:
        print('call_id:',call_id)
        conn= connect_database()
        cursor= conn.cursor()
        call_data= cursor.execute(f"select call_id,translated_transcript from TBL_call_details where call_id = '{call_id}'").fetchall()
        conn.close()

        if not get_call_summary(call_data):
            return False
        
    return True