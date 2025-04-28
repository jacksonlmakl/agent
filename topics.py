from transformers import AutoModelForSequenceClassification, TFAutoModelForSequenceClassification
from transformers import AutoTokenizer
import numpy as np
from scipy.special import expit

def topics(text):
    MODEL = f"cardiffnlp/tweet-topic-latest-multi"
    tokenizer = AutoTokenizer.from_pretrained(MODEL)

    # PT
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)
    class_mapping = model.config.id2label

    
    tokens = tokenizer(text, return_tensors='pt')
    output = model(**tokens)

    scores = output[0][0].detach().numpy()
    scores = expit(scores)
    predictions = (scores >= 0.5) * 1


    # TF
    output=[]
    for i in range(len(predictions)):
        if predictions[i]:
            print(class_mapping[i])
            output.append(class_mapping[i])
    return output