from transformers import AutoModelForSequenceClassification
from transformers import AutoTokenizer
import numpy as np
from scipy.special import expit
import torch

def topics(text, model_name=None):
    MODEL = "cardiffnlp/tweet-topic-latest-multi"
    if model_name:
        MODEL = model_name
    
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)
    
    # Move model to the appropriate device
    model = model.to(device)
    
    # Get the class mapping
    class_mapping = model.config.id2label

    # Tokenize with proper parameters to handle variable length
    tokens = tokenizer(text, return_tensors='pt', truncation=True, padding='max_length', max_length=512)
    
    # Move input tensors to the same device as the model
    tokens = {k: v.to(device) for k, v in tokens.items()}
    
    # Get model output
    with torch.no_grad():  # Add this to avoid unnecessary gradient computation
        output = model(**tokens)

    # Process outputs
    scores = output[0][0].cpu().numpy()  # Move back to CPU for numpy operations
    scores = expit(scores)
    predictions = (scores >= 0.5) * 1

    # Build output list of topics
    output = []
    for i in range(len(predictions)):
        if predictions[i]:
            output.append(class_mapping[i])
            
    return output