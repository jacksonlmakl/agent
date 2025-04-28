from lightweight import chat
from search import chat as search
from topics import topics
from rag import RAG
import datetime



class Agent:
     def __init__(self):
          self.messages=[]

     def chat(self,prompt,web=None,rag=None):
          context=[]
          if rag:
               r=RAG(prompt)
               context.append(r)
          if web:
               s=search(prompt)
               context.append(s)    
                     
          c=chat(f"""
               User Question/Prompt:
                    - ''{prompt}''
               Instructions:
                    {'- Use the unstructured text information provided below to inform your response to the user prompt' if rag ==True or web==True else ''}
                    - Be concise, accurate, and coherent in your answers
               {'Contextual Information:' if rag ==True or web==True else ''}
               {'\n'.join(context)}
               """)
          t=topics(c)

          user_entry={
               "timestamp": str(datetime.datetime.now()),
               "topics": t,
               "role":"user",
               "content": prompt
          }
          self.messages.append(user_entry)

          assistant_entry={
               "timestamp": str(datetime.datetime.now()),
               "topics": t,
               "role":"assistant",
               "content": c
          }
          self.messages.append(assistant_entry)
          return assistant_entry
          

