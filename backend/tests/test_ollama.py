import ollama

response = ollama.chat(
    model="qwen2.5:3b-instruct",
    messages=[
        {
            "role": "user",
            "content": "What is PM-KISAN? Explain in 2 simple sentences."
        }
    ]
)

print("\nQwen Response:\n")
print(response["message"]["content"])