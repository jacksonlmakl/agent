from transformers import AutoModelForSequenceClassification, TFAutoModelForSequenceClassification
from transformers import AutoTokenizer
import numpy as np
from scipy.special import expit

def topics(text, model_name=None):
    MODEL = "cardiffnlp/tweet-topic-latest-multi"
    if model_name:
        MODEL = model_name
    tokenizer = AutoTokenizer.from_pretrained(MODEL)

    # PT
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)
    class_mapping = model.config.id2label

    # Add truncation=True and padding='max_length' to handle variable length inputs
    tokens = tokenizer(text, return_tensors='pt', truncation=True, padding='max_length', max_length=512)
    output = model(**tokens)

    scores = output[0][0].detach().numpy()
    scores = expit(scores)
    predictions = (scores >= 0.5) * 1

    # TF
    output = []
    for i in range(len(predictions)):
        if predictions[i]:
            output.append(class_mapping[i])
    return output