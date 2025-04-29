import json
import os


def process_chats():
    chats=os.listdir('chats')
    chat_data={}
    auto_chat_data={}
    for path in chats:
        with open(f"chats/{path}",'r') as f:
            if 'auto_chat' in path:
                _temp=json.loads(f.read())
                chat_data.update({path.split('__')[-1].split('.json')[0]:_temp})
            else:
                _temp=json.loads(f.read())
                auto_chat_data.update({path.split('__')[-1].split('.json')[0]:_temp})

    chat_data = [
        x
        for xs in list(chat_data.values())
        for x in xs
    ]
    chat=[]
    for row in chat_data:
        _temp={}
        _temp['role']='user'
        _temp['content']=row['user']
        chat.append(_temp)
        _temp={}
        _temp['role']='assistant'
        _temp['content']=row['assistant']
        chat.append(_temp)
    auto_chat=list(auto_chat_data.values())[0]
    return (chat,auto_chat)
