from agent import Agent, autoChat
from questions import question
import threading
import time

class Model:
    def __init__(self):        
        self.agent = Agent()
        self.conscious = []
        self.subconscious = []
        self.threads = []
        self.lock = threading.Lock()  # Add a lock for thread safety

    def chat(self, prompt, web=False, rag=False, tokens=150, use_gpt=False,use_sub_gpt=True, iters=5):
        response = self.agent.chat(prompt=prompt,
                                  web=web,
                                  rag=rag,
                                  tokens=tokens,
                                  use_gpt=use_gpt,
                                  messages=self.conscious[-5:])

        generated_questions = question(response)
        
        # Create a semaphore that allows max 3 concurrent threads
        max_threads = 3
        semaphore = threading.Semaphore(max_threads)

        # Clear previous threads
        self.threads = []

        # Define the worker function correctly
        def thread_worker(q, semaphore):
            with semaphore:  # Acquire the semaphore
                result = autoChat(q, None, iters, 75, True, False, use_sub_gpt)
                # Safely add to subconscious using lock
                with self.lock:
                    self.subconscious.append(result)

        # Create threads with the properly defined worker
        for q in generated_questions:
            thread = threading.Thread(
                target=thread_worker,
                args=(q, semaphore)
            )
            self.threads.append(thread)
            thread.start()  # Start the thread immediately

        self.conscious.append({"role": "user", "content": prompt})
        self.conscious.append({"role": "assistant", "content": response})  # Changed "user" to "assistant"
        
        return response