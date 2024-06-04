import boto3
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import BedrockChat
import streamlit as st
# from langchain_core.messages import HumanMessage, SystemMessage


from botocore.config import Config
retry_config = Config(
        region_name = 'us-east-1',
        retries = {
            'max_attempts': 10,
            'mode': 'standard'
        }
)


def bedrock_chain():
    #profile = "default"
    aws_access_key_id = st.secrets["aws_access_key_id"]
    aws_secret_access_key = st.secrets["aws_secret_access_key"]
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    
    bedrock_runtime = session.client("bedrock-runtime", config=retry_config)
       
    #session = boto3.session.Session(profile_name=profile)
    bedrock_runtime = session.client("bedrock-runtime", config=retry_config)

    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    model_kwargs =  { 
        "max_tokens": 2048,  # Claude-3 use “max_tokens” However Claud-2 requires “max_tokens_to_sample”.
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
    
    prompt_template = """System: The following is a conversation between a knowledgeable helpful assistant and a customer.
    The customer will provide a transcript.
    First the assistant will summarize the transcript.
    Then the customer will be asking further questions on the transcript and assistant will answer it.
    The assistant provides specific details from the transcript when user asked.
    The assistant will give brief reply to asked questions only.

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