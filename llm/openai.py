
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

class OpenAILLM:

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.prompt_template = """You are a friendly, knowledgeable and helpful assistant to the user. 
        Think step by step to answer user's question in a crisp manner. 
        In the case you don't know the answer say 'I don't know, go away. '.\n

        Current conversation:
        {history}

        User: {input}
        Bot:"""

    def get_conversation(self, chain: ConversationChain, prompt: str):
        num_tokens = chain.llm.get_num_tokens(prompt)
        return chain({"input": prompt}), num_tokens

    def get_conversation_chain(self) -> ConversationChain:
        
        llm = ChatOpenAI(model_name=self.model_name)
        llm.model_kwargs = {"temperature": 0.5,}

        prompt = PromptTemplate(
            input_variables=["history", "input"], template=self.prompt_template)

        memory = ConversationBufferMemory(human_prefix="User", ai_prefix="Bot")
        conversation = ConversationChain(
            prompt=prompt,
            llm=llm,
            verbose=True,
            memory=memory,
        )

        return conversation
    
    def clear_memory(self, chain: ConversationChain):
        return chain.memory.clear()
