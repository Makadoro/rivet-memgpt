import gradio as gr
import requests
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()
# Get openai key from environment variable
api_key = os.getenv("OPEN_AI_KEY")
client = OpenAI(api_key=api_key)

# Functions
# ---------------
def on_load(msg, chatbot, audio):
    return respond("Event: User just logged in", None, False, True)

def respond(message, chat_history, audio, start_conversation=False):
    if chat_history is None:
        chat_history = []    
    message = retrieve_message(message, audio)
    # Do not add empty messages
    if not message:
        return None, chat_history, None
    bot_message = request_api(message, start_conversation)

    # playback audio
    response_content = text_to_speech(bot_message)
    voice = response_content.content

    # Save the voice data to a file
    with open('voice.mp3', 'wb') as f:
        f.write(voice)

    chat_history.append((message, bot_message))
    # print(chat_history)
    return "", chat_history, None, 'voice.mp3'

# Get message either from text or audio
def retrieve_message(message, audio):
    # Get the user input either from audio or from text
    if audio:
        user_input = transcribe_audio(audio)
    else:
        user_input = message
    # Return the assistants input here
    return user_input

# Use openai to transcribe audio file
def transcribe_audio(audio):
    audio_file = open(audio, "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    # print(transcript.text)
    return transcript.text

def text_to_speech(bot_message):
    response = client.audio.speech.create(
        model="tts-1",
        voice = "alloy",
        input = bot_message
    )
    return response

# Request node js api to get response from rivet
def request_api(message, start_conversation):
    data = {
        "message": message, 
        "start_conversation": start_conversation
    }
    json_data = json.dumps(data)
    print(json_data)
    response = requests.post(
        "http://localhost:8085/message",
        data=json_data,
        headers={"Content-Type": "application/json"},
    )
    # print("This is the response: " + str(response.json()))
    return response.json().get('message', {})

# Gradio Chat Interface
# ---------------
with gr.Blocks() as chat:
    gr.Markdown(
        """
        # Rivet MemGPT Chat
        ### Note: Press "Start Conversation" first before you start chatting
        Write /exit to properly end the conversation (AI will then create a summary and remember informations)
        """
    )
    start = gr.Button("Start conversation")
    chatbot = gr.Chatbot()

    with gr.Row():
        
        with gr.Column(scale=7):
            msg = gr.Textbox(show_label=False, placeholder='Enter your response here or use audio input')
            audio = gr.Audio(sources=["microphone"], label="Speak", type="filepath")
        
        submit = gr.Button("Submit", scale=3)
        
    ai = gr.Audio(format='mp3', interactive = False, container = True, value=None, label="AI response (audio)", autoplay=True)
    
    # Events
    submit.click(fn=respond, inputs=[msg, chatbot, audio], outputs=[msg, chatbot, audio, ai])
    msg.submit(respond, [msg, chatbot, audio], [msg, chatbot, audio])
    start.click(fn=on_load, inputs=[msg, chatbot, audio], outputs=[msg, chatbot, audio, ai])

chat.launch(share=False, show_api=False)