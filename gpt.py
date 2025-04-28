from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
import time

def gpt(prompt):
    count=1
    while True:
        try:
            client = OpenAI()
            response = client.responses.create(
                model="gpt-4.1",
                input=prompt
            )
            break
        except:
            time.sleep(10)
            count+=1
            if count ==6:
                return "Error"
            continue

    return response.output_text
