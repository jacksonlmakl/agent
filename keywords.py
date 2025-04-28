from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

def keywords(text,model_name = "agentlans/flan-t5-small-keywords"):
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    input_text = text
    inputs = tokenizer(input_text, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=512)
    decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Process the output to get a list of keywords (split and remove duplicates)
    keywords = list(set(decoded_output.split('||')))
    print(keywords)
    return keywords
