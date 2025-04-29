import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig
import gc
from rag import RAG
# Global cache to avoid reloading the model
model_cache = {}

def chat(prompt, model_path="./qwen3-1.7b-finetuned-final", max_new_tokens=200, temperature=0.7, context=[],rag=False):
    """
    Generate responses using your fine-tuned Qwen model.
    
    Args:
        prompt (str): The user's query or prompt
        model_path (str): Path to your fine-tuned model
        max_new_tokens (int): Maximum number of tokens to generate
        temperature (float): Controls randomness (lower = more deterministic)
        context (list): Previous conversation context in the format of 
                        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    
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
    if model_path not in model_cache:
        print(f"Loading fine-tuned model from {model_path} on {device}")
        
        # Load the base model info
        try:
            config = PeftConfig.from_pretrained(model_path)
            base_model_name = config.base_model_name_or_path
            print(f"Detected base model: {base_model_name}")
        except:
            # If not a PEFT model, assume it's a full model
            base_model_name = "Qwen/Qwen3-1.7B"  # Default base model
            print(f"Using default base model: {base_model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        
        # Load model - try both approaches
        try:
            # First try loading as a directly saved model
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if device in ["cuda", "mps"] else torch.float32,
                device_map=device
            )
            print("Loaded fine-tuned model directly")
        except:
            # If that fails, load as a PEFT/LoRA model
            print("Loading as PEFT model...")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16 if device in ["cuda", "mps"] else torch.float32,
                device_map=device
            )
            model = PeftModel.from_pretrained(base_model, model_path)
            print("Loaded model with LoRA weights")
        
        # Set to evaluation mode
        model.eval()
        
        # Store in cache
        model_cache[model_path] = (model, tokenizer)
    else:
        model, tokenizer = model_cache[model_path]
    
    # Prepare conversation for Qwen format
    # Start with system message if not in context
    if not any(msg.get("role") == "system" for msg in context):
        messages = [{"role": "system", "content": "You are a helpful assistant. You are smart, analytical, and great at communicating."}]
    else:
        messages = []
    
    # Add existing context
    messages.extend(context)
    #RAG
    if rag:
        information=RAG(prompt=prompt)
        messages.append({"role": "system", "content": f"""
                         Instructions:
                         - You will use the information below to inform you response to the user prompt.
                         - If information is not relevant to the prompt, ignore it.
                         - Your response should be clear, cohesive, and coherent.

                         Information
                         ```{information}```
                        """})
    # Add current prompt
    messages.append({"role": "user", "content": prompt})
    
    # Format conversation using the chat template
    chat_text = tokenizer.apply_chat_template(messages, tokenize=False)
    
    # Tokenize input
    inputs = tokenizer(chat_text, return_tensors="pt").to(device)
    
    # Clear cache if needed
    if device == "cuda":
        torch.cuda.empty_cache()
    elif device == "mps" and hasattr(torch.mps, 'empty_cache'):
        torch.mps.empty_cache()
    
    # Generate with appropriate parameters
    with torch.no_grad():
        output = model.generate(
            inputs.input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            top_k=40,
            repetition_penalty=1.2,
            pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id,
        )
    
    # Extract the model's response
    full_output = tokenizer.decode(output[0], skip_special_tokens=True)
    
    # Extract just the assistant's response from the full output
    try:
        # If using the Qwen format, the response should be after the last instance
        # of the user's message
        if prompt in full_output:
            response = full_output.split(prompt)[-1].strip()
        elif "assistant" in full_output.lower():
            # Try to get content after the last 'assistant' marker
            response = full_output.split("assistant")[-1].strip()
            # Remove any leading colons or whitespace
            response = response.lstrip(": \n")
        else:
            # Just return everything after the input (this is a fallback)
            response = full_output[len(chat_text):].strip()
    except Exception as e:
        print(f"Error extracting response: {e}")
        response = full_output
    
    # If we still don't have a response, return the full output
    if not response:
        response = full_output
    
    # Clean up any garbage collection
    gc.collect()
    
    return response.replace("</think>","")