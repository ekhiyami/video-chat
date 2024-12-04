import boto3
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import BedrockChat
import streamlit as st



from botocore.config import Config
retry_config = Config(
        region_name = 'us-east-1',
        retries = {
            'max_attempts': 10,
            'mode': 'standard'
        }
)


def bedrock_chain():
    ACCESS_KEY = st.secrets["ACCESS_KEY"]
    SECRET_KEY = st.secrets["SECRET_KEY"]
    session = boto3.Session(
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    
 
    bedrock_runtime = session.client("bedrock-runtime", config=retry_config)
       
    model_id = "us.amazon.nova-micro-v1:0"
    model_kwargs =  { 
        "max_tokens": 2048,  
        "temperature": 0.0,
        "top_k": 250,
        "top_p": 1,
        "stop_sequences": ["\n\nHuman"],
    }
    model = BedrockChat(
        client=bedrock_runtime,
        model_id=model_id,
        model_kwargs=model_kwargs,
    )
    
    prompt_template = """System: I want you to provide a comprehensive summary of this text provided, and then list the key points. Finally, write a short conclusion about what the video is about.

    Current conversation:
    {history}

    User: {input}
    Bot:"""
    prompt = PromptTemplate(
        input_variables=["history", "input"], template=prompt_template
    )

    memory = ConversationBufferMemory(human_prefix="User", ai_prefix="Bot")
    conversation = ConversationChain(
        prompt=prompt,
        llm=model,
        verbose=True,
        memory=memory,
    )
    return conversation


def run_chain(chain, prompt):
    return chain({"input": prompt})


def clear_memory(chain):
    return chain.memory.clear()
