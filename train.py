from transformers import Trainer, TrainingArguments, AutoModelForCausalLM, AutoTokenizer, DefaultDataCollator
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import torch
import gc
import os
from process_chats import process_chats

# Configure memory management for MPS
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.8"
os.environ["PYTORCH_MPS_LOW_WATERMARK_RATIO"] = "0.5"

# Helper function for memory cleanup
def cleanup_memory():
    gc.collect()
    if hasattr(torch.mps, 'empty_cache'):
        torch.mps.empty_cache()
    elif torch.cuda.is_available():
        torch.cuda.empty_cache()

# Set a small max sequence length to reduce memory usage
max_length = 128

# Determine device - use CPU if MPS causes issues
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using device: {device}")

# Create some sample conversations if process_chats isn't available
# Replace this with process_chats() if you have that function
sample_conversations = process_chats()

# Load model and tokenizer
print("Loading tokenizer and model...")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-1.7B")
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-1.7B",
    torch_dtype=torch.float16,
    device_map=device
)
cleanup_memory()

# Process conversations
print("Processing conversations...")
processed_data = []

def format_for_qwen(conversation):
    # Apply chat template to convert to the format Qwen expects
    text = tokenizer.apply_chat_template(
        conversation,
        tokenize=False
    )
    
    # Tokenize with explicit padding and truncation
    encoded = tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt"
    )
    
    return {
        "input_ids": encoded["input_ids"][0],
        "attention_mask": encoded["attention_mask"][0],
        "labels": encoded["input_ids"][0].clone()
    }

for i, conv in enumerate(sample_conversations):
    processed_data.append(format_for_qwen(conv))
    print(f"Processed conversation {i+1}/{len(sample_conversations)}")
    cleanup_memory()

# Create dataset
def create_dataset(processed_data):
    return Dataset.from_dict({
        "input_ids": [item["input_ids"].tolist() for item in processed_data],
        "attention_mask": [item["attention_mask"].tolist() for item in processed_data],
        "labels": [item["labels"].tolist() for item in processed_data]
    })

train_dataset = create_dataset(processed_data)
print(f"Created dataset with {len(train_dataset)} examples")

# Set model to training mode first
model.train()

# Configure LoRA to target all projection matrices
lora_config = LoraConfig(
    r=4,  # Slightly larger rank
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # Target all projection matrices
    lora_dropout=0.0,
    bias="none",
    task_type="CAUSAL_LM"  # Explicitly set task type
)

# Properly prepare model for training
model = get_peft_model(model, lora_config)
print("Applied LoRA to model")

# Verify trainable parameters
trainable_params = 0
all_params = 0
for name, param in model.named_parameters():
    num_params = param.numel()
    all_params += num_params
    if param.requires_grad:
        trainable_params += num_params
        
print(f"Trainable parameters: {trainable_params:,} ({100 * trainable_params / all_params:.2f}% of all parameters)")

# Explicitly make sure LoRA parameters require gradients
for name, param in model.named_parameters():
    if 'lora' in name:
        param.requires_grad = True

cleanup_memory()

# Training arguments with gradient checkpointing disabled
training_args = TrainingArguments(
    output_dir="./qwen3-1.7b-finetuned",
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=1,
    learning_rate=2e-4,
    weight_decay=0.01,
    adam_beta2=0.95,
    save_steps=10,
    logging_steps=1,
    optim="adamw_torch",
    gradient_checkpointing=False,  # Disabled to avoid gradient issues
    max_grad_norm=0.3,
    disable_tqdm=False,  # Enable progress tracking
    report_to="none",  # Disable reporting to save memory
)

data_collator = DefaultDataCollator()

print("Starting training...")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    data_collator=data_collator,
)

# Final cleanup before training
cleanup_memory()

# Run training
trainer.train()
# Save the trained model
print("Saving model...")
trainer.save_model("./qwen3-1.7b-finetuned-final")
print("Training completed successfully!")