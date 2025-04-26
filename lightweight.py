import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def lightweight(prompt,model_name="facebook/opt-125m"):

    # Determine device (works on both Mac and Ubuntu)
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"  # Apple Silicon
    else:
        device = "cpu"

    print(f"Loading model {model_name} on {device}")

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device in ["cuda", "mps"] else torch.float32,
        low_cpu_mem_usage=True
    )
    model.to(device)

    # Generate response
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.generate(
            inputs.input_ids,
            max_length=inputs.input_ids.shape[1] + 100,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    # Extract new text
    full_response = tokenizer.decode(output[0], skip_special_tokens=True)
    model_response = full_response[len(prompt):].strip()

    print(f"Response: {model_response}")
    return model_response
lightweight("Write a haiku about fruit.")