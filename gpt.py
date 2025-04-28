from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

def gpt(prompt):
    client = OpenAI()
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )

    return response.output_text
