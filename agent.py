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
               s=search(prompt,use_gpt=use_gpt)
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
               print("USING CHAT GPT 4")
          else:
               c=chat(_prompt,max_new_tokens=tokens,context=messages)
        
          t=topics(c)
          k=keywords(c)

          entry={
               "meta":{"timestamp": str(datetime.datetime.now()),
               "topics": t,
               "key_words":k,
               "web": web,
               "rag": rag},
               "items":[{"role":"user","content":prompt},{"role":"assistant","content":c}]
          }
          self.messages.append(entry)
          return entry['items'][-1]['content']
     


from agent import Agent

def autoChat(starter,instructions=None,iters=5,tokens=100,web=False,rag=False,use_gpt=False):
    a=Agent()
    a1=Agent()
    if instructions:
        base=instructions
    else:
        base="""
        Instructions:
          - Engage naturally as if you are having a real conversation.
          
          - If you need outside information to answer properly, say exactly: "I require information from the web"

          - Ask thoughtful questions to stay involved and deepen the discussion.

          - Feel free to explore your partner's ideas or shift the topic as you see fit.

          - You control the flow of the conversation — continue, pivot, or expand topics at your discretion.

          - Respond fully and clearly, using plain text only.          
        """
    prompt_a=f""" 
    {base} 
    Conversation Prompt:
    {starter}
    """
    chat_history=[]
    count=0
    _rag=False
    _web=False
    while True:
        if rag == True:
            if count%3==0 or count==0 :
                _rag=True
            else:
                _rag=False
        if web == True:
            if count%3==0 or count==0 :
                _web=True
            else:
                _web=False
        if "i require information from the web" in prompt_a.strip().replace("  "," ").lower() and web==True:
            print("Agent searching the web.....")
            _web=True
        prompt_a1=a.chat(base+prompt_a,web=_web,rag=_rag,tokens=tokens,messages=a1.messages,use_gpt=use_gpt)
        if "i require information from the web" in prompt_a1.strip().replace("  "," ").lower() and web==True:
            print("Agent 1 searching the web.....")
            _web=True
        prompt_a=a1.chat(base+prompt_a1,web=_web,rag=_rag,tokens=tokens,messages=a.messages,use_gpt=use_gpt)
        print("\nAgent A1: ",prompt_a1)
        print("\nAgent A: ",prompt_a)
        chat_history.append({
            "user":prompt_a1,
            "assistant":prompt_a
        })
        print('\n\n')
        count+=1
        if count ==iters:
            break
    return chat_history

