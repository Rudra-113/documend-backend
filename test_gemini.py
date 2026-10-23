from app.gemma import ask_gemini

response = ask_gemini(
    "Explain in one sentence what a hospital bill is."
)

print(response)