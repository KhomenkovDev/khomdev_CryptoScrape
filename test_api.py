from google import genai
import os
from config import settings
client = genai.Client(api_key=settings.GEMINI_API_KEY)
print(client.models.generate_content(model="gemini-2.5-flash", contents="hello").text)
