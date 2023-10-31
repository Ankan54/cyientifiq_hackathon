from batch_transcript import batch_transcript
from parse_transcript import parse_transcript
#from execute_stored_proc import execute_stored_proc
import time


def main(src_container_sas,dest_container_sas,language):
    if len(language) <= 0:
        print('Error: Invalid language')
        return False
    
    batch_transcript_result= None
    start_time =time.time()

    batch_transcript_result= batch_transcript(src_container_sas,dest_container_sas,language)
    #batch_transcript_result = 'c8ae4978-08f5-40b8-83aa-5e39382d8b46'
    end_time =time.time()
    print("batch transcription time:", str(end_time-start_time))

    if batch_transcript_result == False:
        print('Error: Failed creating audio transcript')
        return False

    if not parse_transcript(batch_transcript_result,language):
        print('Error: Failed parsing audio transcript')
        return False

    return True
    
if __name__ == "__main__":
    src_container_sas= ''
    dest_container_sas= ''
    language= 'english'
    try:
        if not main(src_container_sas,dest_container_sas,language):
            raise Exception('Process ended with Error')
        else:
            print('Done!')
    except Exception as e:
        print('Error:', str(e))