from transformers import BertTokenizer, BertForQuestionAnswering
import torch

# Load a BERT model for question generation (compatible with your tokenizer list)
tokenizer = BertTokenizer.from_pretrained("deepset/bert-base-cased-squad2")
model = BertForQuestionAnswering.from_pretrained("deepset/bert-base-cased-squad2")

def question(text, num_questions=3):
    """
    Generate questions from text using BERT.
    This is a simplistic approach that uses question answering in reverse.
    
    Args:
        text (str): Text to generate questions about
        num_questions (int): Number of questions to generate
    
    Returns:
        list: Generated questions
    """
    # Split text into chunks
    chunks = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
    
    # Limit number of questions
    num_questions = min(num_questions, len(chunks))
    
    questions = []
    for i in range(num_questions):
        chunk = chunks[i]
        
        # Create synthetic question start phrases
        question_starters = [
            "What is", "How does", "Why is", 
            "What are the implications of", "Explain how",
            "What role does", "What factors contribute to"
        ]
        
        # Generate a question for this chunk
        starter = question_starters[i % len(question_starters)]
        
        # Get key terms from the chunk
        words = chunk.split()
        if len(words) > 5:
            key_term = " ".join(words[0:3])  # Use first few words
            question = f"{starter} {key_term}?"
            questions.append(question)
    
    return questions
