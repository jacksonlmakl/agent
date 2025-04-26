import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import time

class LightweightChatLLM:
    """
    A lightweight chat-based LLM implementation for MacBooks with limited RAM.
    This class handles loading a small model, optimizing it for Apple Silicon,
    and providing a simple interface for chat interactions.
    """
    
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0", use_gpu=True):
        """
        Initialize the chat model.
        
        Args:
            model_name: The Hugging Face model name to load
            use_gpu: Whether to use MPS (Apple GPU) acceleration
        """
        self.device = "mps" if use_gpu and torch.backends.mps.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load model with lower precision for memory efficiency
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "mps" else torch.float32,
            low_cpu_mem_usage=True
        )
        self.model.to(self.device)
        
        # Enable optimizations
        if hasattr(self.model, "enable_attention_slicing"):
            self.model.enable_attention_slicing()
        
        # Chat history for context
        self.chat_history = []
        
    def generate_response(self, user_input, max_length=1024, temperature=0.7):
        """
        Generate a response to the user input.
        
        Args:
            user_input: The user's message
            max_length: Maximum number of tokens to generate
            temperature: Controls randomness (lower = more deterministic)
            
        Returns:
            The model's response
        """
        # Append user input to chat history
        self.chat_history.append(f"User: {user_input}")
        
        # Format chat history as context for the model
        prompt = self._format_prompt(user_input)
        
        # Tokenize input and move to device
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Measure generation time
        start_time = time.time()
        
        # Generate response
        with torch.no_grad():
            output = self.model.generate(
                inputs.input_ids,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode the response and remove the input part
        full_output = self.tokenizer.decode(output[0], skip_special_tokens=True)
        response = full_output[len(prompt):].strip()
        
        # Calculate tokens per second
        elapsed_time = time.time() - start_time
        num_tokens = len(output[0]) - len(inputs.input_ids[0])
        tokens_per_second = num_tokens / elapsed_time
        
        print(f"Generated {num_tokens} tokens in {elapsed_time:.2f} seconds ({tokens_per_second:.2f} tokens/sec)")
        
        # Add response to chat history
        self.chat_history.append(f"Assistant: {response}")
        
        return response
    
    def _format_prompt(self, user_input):
        """
        Format the prompt using the chat history and current user input.
        Specific formatting depends on the model being used.
        """
        # TinyLlama chat format (adjust for other models as needed)
        formatted_history = "\n".join(self.chat_history[-6:-1]) if len(self.chat_history) > 1 else ""
        
        if formatted_history:
            return f"{formatted_history}\nUser: {user_input}\nAssistant:"
        else:
            return f"User: {user_input}\nAssistant:"
    
    def clear_history(self):
        """Clear the chat history."""
        self.chat_history = []


def main():
    """Main function to demonstrate usage of the LightweightChatLLM class."""
    print("Initializing lightweight LLM chat model...")
    
    # You can choose from these models depending on your performance needs:
    # - "TinyLlama/TinyLlama-1.1B-Chat-v1.0" (smallest)
    # - "microsoft/phi-2" (good balance of size/quality)
    # - "Qwen/Qwen1.5-0.5B-Chat" (another lightweight option)
    # - "EleutherAI/gpt-neo-125m" (very small but basic)
    
    chat_model = LightweightChatLLM(model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    
    print("\nChat model ready! Type 'exit' to quit, 'clear' to clear chat history.")
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            break
        elif user_input.lower() == 'clear':
            chat_model.clear_history()
            print("Chat history cleared.")
            continue
        
        print("\nThinking...")
        response = chat_model.generate_response(user_input)
        print(f"\nAssistant: {response}")


if __name__ == "__main__":
    main()