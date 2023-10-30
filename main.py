from batch_transcript import batch_transcript
from parse_transcript import parse_transcript
from execute_stored_proc import execute_stored_proc
import time


def main(src_container_sas,dest_container_sas,language):
    if len(language) <= 0:
        print('Error: Invalid language')
        return False
    
    batch_transcript_result= None
    start_time =time.time()

    batch_transcript_result= batch_transcript(src_container_sas,dest_container_sas,language)
    end_time =time.time()
    print("batch transcription time:", str(end_time-start_time))

    if batch_transcript_result == False:
        print('Error: Failed creating audio transcript')
        return False

    return True
    
if __name__ == "__main__":
    src_container_sas= ''
    dest_container_sas= ''
    language= 'hindi'
    try:
        if not main(src_container_sas,dest_container_sas,language):
            raise Exception('Process ended with Error')
        else:
            print('Done!')
    except Exception as e:
        print('Error:', str(e))