# from openai import OpenAI

# def call_deepseek_api(messages):
#     client = OpenAI(
#         api_key=os.getenv("DEEPSEEK_API_KEY"),
#         base_url="https://api.deepseek.com"
#     )
    
#     try:
#         response = client.chat.completions.create(
#             model="deepseek-chat",
#             messages=messages,
#             stream=False
#         )
        
#         return response.choices[0].message.content
        
#     except Exception as e:
#         return f"Error occurred during API call: {str(e)}"

# def chatting_main(prompt_path="./prompt/prompt_5_chatting.md"):
#     try:
#         # Read system prompt from file
#         with open(prompt_path, "r", encoding="utf-8") as f:
#             system_prompt = f.read()
        
#         # Initialize conversation history with system prompt
#         conversation_history = [{"role": "system", "content": system_prompt}]
        
#         print("Multi-turn conversation started! Type 'end' to exit the conversation.\n")
        
#         while True:
#             # Get user input
#             user_input = input("User: ").strip()
            
#             # Check if user wants to end the conversation
#             if user_input.lower() in ['end', 'exit', 'quit', 'bye', 'goodbye']:
#                 print("Conversation ended. Goodbye!")
#                 break
            
#             # Add user message to conversation history
#             conversation_history.append({"role": "user", "content": user_input})
            
#             # Call API with entire conversation history
#             response = call_deepseek_api(conversation_history)
            
#             # Add assistant response to conversation history
#             conversation_history.append({"role": "assistant", "content": response})
            
#             # Print assistant response
#             print(f"Assistant: {response}\n")
            
#     except Exception as e:
#         return f"Error reading prompt file: {str(e)}"
    
# def chatting(query, prompt_path="./prompt/prompt_5_chatting.md"):
#     try:
#         # Read system prompt from file
#         with open(prompt_path, "r", encoding="utf-8") as f:
#             prompt_content = f.read()
        
#         # Call the core API function
#         return call_deepseek_api(prompt_content, query)
        
#     except Exception as e:
#         return f"Error reading prompt file: {str(e)}"

# if __name__ == "__main__":
#     chatting_main()

import os
from openai import OpenAI

def call_deepseek_api(messages):
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error occurred during API call: {str(e)}"

def chatting(query, prompt_path="./prompt/prompt_5_chatting.md"):
    try:
        # Read system prompt from file
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
        
        # Initialize conversation history with system prompt
        conversation_history = [{"role": "system", "content": system_prompt}]
        
        # Add the first test query to conversation history
        conversation_history.append({"role": "user", "content": query})
        
        # Get first response
        first_response = call_deepseek_api(conversation_history)
        conversation_history.append({"role": "assistant", "content": first_response})
        
        print(f"User: {query}")
        print(f"Assistant: {first_response}\n")
        print("Multi-turn conversation started! Type 'end' to exit the conversation.\n")
        
        while True:
            # Get user input
            user_input = input("User: ").strip()
            
            # Check if user wants to end the conversation
            if user_input.lower() in ['end', 'exit', 'quit', 'bye', 'goodbye']:
                print("Conversation ended. Goodbye!")
                break
            
            # Add user message to conversation history
            conversation_history.append({"role": "user", "content": user_input})
            
            # Call API with entire conversation history
            response = call_deepseek_api(conversation_history)
            
            # Add assistant response to conversation history
            conversation_history.append({"role": "assistant", "content": response})
            
            # Print assistant response
            print(f"Assistant: {response}\n")
            
    except Exception as e:
        return f"Error reading prompt file: {str(e)}"

if __name__ == "__main__":
    # Test query
    test_query = "Hello, can you introduce yourself?"
    chatting(test_query)