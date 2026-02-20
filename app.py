import os
import json
import requests
from dotenv import load_dotenv
from pypdf import PdfReader
import gradio as gr
from openai import OpenAI
from agents import Agent, Runner, trace

# Load environment variables
load_dotenv(override=True)

# Setup OpenAI API directly
openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=openai_api_key
)

# ---------- Pushover integration ----------
def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

# ---------- Assistant Class ----------
class Me:

    def __init__(self):
        self.client = client
        self.name = "Fares"

        # Load LinkedIn PDF
        reader = PdfReader("me/Profile.pdf")
        reader1 = PdfReader("me/Fares_Resume .pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        for page in reader1.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text        

        # Load Summary
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, " \
                        f"particularly questions related to {self.name}'s career, background, skills and experience. " \
                        f"Your responsibility is to represent {self.name} faithfully. " \
                        f"If you don't know the answer, use the record_unknown_question tool. " \
                        f"Try to steer users towards leaving their email, and record it with record_user_details."

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        return system_prompt
    
    # 1. ADDED 'async' HERE
    async def chat(self, message, history):
        # 2. Setup the Agent properly with the system prompt
        my_agent = Agent(
            name="Fares_Assistant", 
            instructions=self.system_prompt(), 
            model="gpt-4o-mini"
        )
        
        # 3. Use await inside the async function
        with trace("Protected Automated SDR", my_agent, message):
            result = await Runner.run(my_agent, message)
            
        return result.final_output
    

if __name__ == "__main__":
    me = Me()
    # Gradio automatically handles async functions!
    gr.ChatInterface(me.chat, type="messages").launch()