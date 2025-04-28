from lightweight import chat
from search import chat as search
from topics import topics
from rag import RAG
import datetime
from gpt import gpt
from keywords import keywords


class Agent:
     def __init__(self):
          self.messages=[]

     def chat(self,prompt,web=False,rag=False,use_gpt=False,tokens=200,messages=[]):
          context=[]
          if rag:
               r=RAG(prompt)
               context.append(r)
          if web:
               s=search(prompt)
               context.append(s)    
                     
          _prompt=f"""
               User Question/Prompt:
                    - ''{prompt}''
               Instructions:
                    {'- Use the unstructured text information provided below to inform your response to the user prompt' if rag ==True or web==True else ''}
                    - Be concise, accurate, and coherent in your answers
               {'Contextual Information:' if rag ==True or web==True else ''}
               {'\n'.join(context)}
               """
          if use_gpt:
               if messages !=[]:
                    _prompt = f"{_prompt} \n\n--------Chat History: \n{str(messages)}"
               c=gpt(_prompt)
               print(c)
          else:
               c=chat(_prompt,max_new_tokens=tokens,context=messages)
        
          t=topics(c)
          k=keywords(c)

          user_entry={
               "timestamp": str(datetime.datetime.now()),
               "topics": t,
               "key_words":k,
               "web": web,
               "rag": rag,
               "role":"user",
               "content": prompt
          }
          self.messages.append(user_entry)

          assistant_entry={
               "timestamp": str(datetime.datetime.now()),
               "topics": t,
               "key_words":k,
               "web": web,
               "rag": rag,
               "role":"assistant",
               "content": c
          }
          self.messages.append(assistant_entry)
          return assistant_entry
          

