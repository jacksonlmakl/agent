from agent import Agent, autoChat
from questions import question
import threading
import time
import uuid  # For generating unique IDs
import json

class Model:
    def __init__(self):        
        self.agent = Agent()
        self.conscious = []
        self.subconscious = []
        self.active_threads = {}  # Dictionary to track active threads with IDs
        self.lock = threading.Lock()  # Add a lock for thread safety
        self.thread_cleanup_interval = 60  # Seconds between thread cleanup
        self.files=[]

        # Start thread monitoring
        self.monitor_thread = threading.Thread(target=self._monitor_threads, daemon=True)
        self.monitor_thread.start()

        self.flush_thread = threading.Thread(target=self._flush, daemon=True)
        self.flush_thread.start()

    def _flush(self):
        while True:
            if len(self.conscious)>=10:
                _temp=self.conscious
                self.conscious=self.conscious[-5:]

                file_path=f"""chats/chat_{str(uuid.uuid4())}__{str(time.time()).replace('.','')}.json"""
                # Save the string to a JSON file
                with open(file_path, 'w') as f:
                    json.dump(_temp,f)
                self.files.append(file_path)
            if len(self.subconscious)>=1:
                _temp=self.subconscious[0]
                self.subconscious=[]
                file_path=f"""chats/auto_chat_{str(uuid.uuid4())}__{str(time.time()).replace('.','')}.json"""
                # Save the string to a JSON file
                with open(file_path, 'w') as f:
                    json.dump(_temp,f)
                self.files.append(file_path)
            
        return 0
    def _monitor_threads(self):
        """Background thread that periodically cleans up completed threads"""
        while True:
            time.sleep(self.thread_cleanup_interval)
            with self.lock:
                # Remove references to completed threads
                completed_threads = [tid for tid, t in self.active_threads.items() if not t.is_alive()]
                for tid in completed_threads:
                    del self.active_threads[tid]

    def chat(self, prompt, web=False, rag=False, tokens=150, use_gpt=False, use_sub_gpt=True, iters=5):
        response = self.agent.chat(prompt=prompt,
                                  web=web,
                                  rag=rag,
                                  tokens=tokens,
                                  use_gpt=use_gpt,
                                  messages=self.conscious)

        generated_questions = question(response)
        
        # Create a semaphore that allows max 3 concurrent threads
        max_threads = 3
        semaphore = threading.Semaphore(max_threads)

        # Define the worker function correctly
        def thread_worker(q, semaphore, thread_id):
            try:
                with semaphore:  # Acquire the semaphore
                    result = autoChat(q, None, iters, 75, True, False, use_sub_gpt)
                    # Safely add to subconscious using lock
                    with self.lock:
                        self.subconscious.append(result)
            except Exception as e:
                print(f"Thread {thread_id} error: {e}")
            finally:
                # Nothing to do here - thread monitoring will clean up references
                pass

        # Create and start threads with the properly defined worker
        new_threads = []
        for q in generated_questions:
            _q = f"""
            Question:
            {q}

            Based On:
            {prompt}
            """
            # Generate a unique ID for this thread
            thread_id = str(uuid.uuid4())
            
            thread = threading.Thread(
                target=thread_worker,
                args=(_q, semaphore, thread_id)
            )
            
            # Track this thread in our dictionary
            with self.lock:
                self.active_threads[thread_id] = thread
                
            thread.start()  # Start the thread immediately
            new_threads.append(thread)  # Keep a local reference for this batch

        self.conscious.append({"role": "user", "content": prompt})
        self.conscious.append({"role": "assistant", "content": response})
        
        return response
        
    def wait_for_all_threads(self, timeout=None):
        """Wait for all background threads to complete, with optional timeout"""
        with self.lock:
            # Make a copy of active threads to avoid modification during iteration
            threads_to_wait = list(self.active_threads.values())
        
        for thread in threads_to_wait:
            thread.join(timeout)
        
        return all(not t.is_alive() for t in threads_to_wait)