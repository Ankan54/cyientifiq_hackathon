# CyientifIQ Innovation League Global Hackathon 2023
## Theme:  Designing Digital Enterprises.

## Title:  AI enabled Open Source Sales Call Analytics Tool.

## 2nd Round: Prototype Development
#### Contains source code for the prototype solution developed.  

## Team: Joyful Jedi

### Owner:
- [@Ankan Bera](https://www.github.com/Ankan54)

## Description
This repository contains the source code for the prototype.  
The prototype has been designed to be run locally, but can easily be resturctured to be deployed into any cloud platform.

For the prototype, we have created the sample audio files ourselves, and due to time and other constraints, some manual intervention regarding uploading the audio files to cloud storage have been kept.  

The code is written using python and for the database we have used locally hosted SQLite3 DB.  
The centralised dashboard for visualisation have been designed in Power BI platform.    


We are using several Azure services APIs and SDKs to create our audio transcripts and analysis data, such as, Azure Storage client, Azure Cognitive services, Azure Translator service, etc. Additionally, Open AI services have been utilized for implementing Generative AI features.

To run the application please follow the below mentioned steps.  
## Installation

Download and Install:   
`python 3.9.6` https://www.python.org/downloads/release/python-396/  
`Visual Studio Code` https://code.visualstudio.com/download

Register for a subscription in Azure Cloud services

Go to https://portal.azure.com/ and 
create the following services:  

`Resource Group`  
`Storage Account`    
`Cognitive Services Multi-Service Account`  
`Speech Service`  
`Translator`  

Register an account in [OpenAI.com](https://www.openai.com) and create an API key.

## Run Locally

Clone the project

```bash
  git clone https://github.com/Ankan54/cyientifiq_hackathon
```

create virtual environment

```bash
  python -m venv venv
  ./venv/Scripts/activate.bat
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Set up Database  
```bash
  python sql_db.py
```

Start the data extraction process

```bash
  python main.py
```

start the Custom Analysis Web App
```bash
  python app.py
```

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`BLOB_STORAGE_KEY`  
`BLOB_STORAGE_NAME`  
`COG_SERVICE_REGION`  
`COG_SERVICE_KEY`  
`SPEECH_TO_TEXT_KEY`  
`TRANSLATOR_KEY`  
`COG_SERVICE_ENDPOINT`  
`TEXT_TRANS_URL`  
`DOC_TRANS_URL`  
`OPENAI_API_KEY`  

