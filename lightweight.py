import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import gc

# Create a model cache to avoid reloading the model
model_cache = {}

def chat(prompt, model_name="meta-llama/Llama-3.2-3B-Instruct", max_new_tokens=200, temperature=0.1, context=[]):
    """
    Generate responses using a lightweight LLM optimized for resource-constrained environments.
    
    Args:
        prompt (str): The user's query or prompt
        model_name (str): Hugging Face model identifier
        max_new_tokens (int): Maximum number of tokens to generate
        temperature (float): Controls randomness (lower = more deterministic)
        
    Returns:
        str: The model's response
    """
    # Determine device (works on both Mac and Ubuntu)
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"  # Apple Silicon
    else:
        device = "cpu"
    
    # Check if model is already loaded
    if model_name not in model_cache:
        print(f"Loading model {model_name} on {device}")
        
        # Load tokenizer with correct padding configuration
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with optimizations
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device in ["cuda", "mps"] else torch.float32,
            low_cpu_mem_usage=True,
        )
        model.to(device)
        
        # Store in cache
        model_cache[model_name] = (model, tokenizer)
    else:
        model, tokenizer = model_cache[model_name]
    
    # Format prompt according to specific model templates
    if "TinyLlama" in model_name and "Chat" in model_name:
        # Use messages format for TinyLlama-Chat
        messages = context+[
            {"role": "system", "content": "You are a helpful, precise, and accurate assistant."},
            {"role": "user", "content": prompt}
        ] 
        
        # Create prompt using model's chat template
        if hasattr(tokenizer, "apply_chat_template"):
            chat_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(chat_text, return_tensors="pt")
        else:
            # Manual template as fallback
            chat_text = f"<|system|>\nYou are a helpful, precise, and accurate assistant.\n<|user|>\n{prompt}\n<|assistant|>"
            inputs = tokenizer(chat_text, return_tensors="pt")
    else:
        # Generic format for other models
        enhanced_prompt = f"""You are a helpful, precise, and accurate assistant. 
Please provide a clear, factual response to the following:

{prompt}

Answer:"""
        inputs = tokenizer(enhanced_prompt, return_tensors="pt")
    
    # Move tensors to the right device
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs.get("attention_mask", None)
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)
    
    # Clear CUDA cache if using GPU
    if device == "cuda":
        torch.cuda.empty_cache()
    
    # Generate with optimal parameters for the model
    with torch.no_grad():
        generate_kwargs = {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "do_sample": True,
            "top_p": 0.95,
            "top_k": 50,
            "repetition_penalty": 1.3,
            "no_repeat_ngram_size": 3,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
            "use_cache": True
        }
        
        if attention_mask is not None:
            generate_kwargs["attention_mask"] = attention_mask
            
        output = model.generate(input_ids, **generate_kwargs)
    
    # Extract the model's response
    input_length = input_ids.shape[1]
    response = tokenizer.decode(output[0, input_length:], skip_special_tokens=True).strip()
    
    # If response is empty, try decoding the entire output
    if not response:
        full_output = tokenizer.decode(output[0], skip_special_tokens=True)
        print(full_output)
        # Try various methods to extract the response
        if "<|assistant|>" in full_output:
            response = full_output.split("<|assistant|>")[-1].strip()
        elif "Answer:" in full_output:
            response = full_output.split("Answer:")[-1].strip()
        elif prompt in full_output:
            response = full_output.split(prompt)[-1].strip()
        else:
            # Just return the last part of the output
            response = full_output[-500:].strip()
    
    return response

