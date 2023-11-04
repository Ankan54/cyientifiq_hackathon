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

class Customer_Analysis(BaseModel):
    '''Customer Analysis from the transcript'''
    Budget: str = Field(description="Did the customer's budget or financial capability come up in the conversation?")
    Authority: str = Field(description="Was there any mention about the customer's decision-making authority?")
    Need: str = Field(description="What needs or pain points of the customer were identified during the call?")
    Timing: str = Field(description="Did the customer mention any specific timeline or urgency related to their purchase decision?")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Provided is the transcript of a credit card sales call between a customer and an agent. Think carefully, and then generate response as instructed"),
    ("human", "{input}")
])

overview_tagging_function = [
    convert_pydantic_to_openai_function(Customer_Analysis)
]
tagging_model = model.bind(
    functions=overview_tagging_function,
    function_call={"name":"Customer_Analysis"}
)
tagging_chain = prompt | tagging_model | JsonOutputFunctionsParser()


def get_cust_analysis(call_data):
    summary_dict_list= []
    for call in call_data:
        try:
            summary_dict = {'call_id': call[0]}
            transcript = call[1]
            cust_analysis_dict = tagging_chain.invoke({"input":f"{transcript}"})

            summary_dict['budget'] = cust_analysis_dict['Budget']
            summary_dict['authority'] = cust_analysis_dict['Authority']
            summary_dict['need'] = cust_analysis_dict['Need']
            summary_dict['timing'] = cust_analysis_dict['Timing']

            summary_dict_list.append(summary_dict)
        
        except Exception as e:
            print('call_id',call[0])
            print('Error:',str(e))
            continue

    print("updating customer analysis...")

    summary_df= pd.DataFrame(summary_dict_list)
    conn= connect_database()
    cursor= conn.cursor()

    for _, row in summary_df.iterrows():
        query = f'''
                UPDATE TBL_call_details
                SET budget = '{row['budget'].replace("'","''")}',
                    authority = '{row['authority'].replace("'","''")}',
                    need = '{row['need'].replace("'","''")}',
                    timing = '{row['timing'].replace("'","''")}',
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


def cust_analysis_main(call_id_list):
    for call_id in call_id_list:
        print('call_id:',call_id)
        conn= connect_database()
        cursor= conn.cursor()
        call_data= cursor.execute(f"select call_id,translated_transcript from TBL_call_details where call_id = '{call_id}'").fetchall()
        conn.close()

        if not get_cust_analysis(call_data):
            return False
        
    return True

# conn= connect_database()
# cursor = conn.cursor()
# call_ids = cursor.execute("select call_id from TBL_call_details").fetchall()
# conn.close()
# call_id_list = [id[0] for id in call_ids]
# print(call_id_list)
# cust_analysis_main(call_id_list)
