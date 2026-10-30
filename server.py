from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
from langchain.chat_models import init_chat_model
from log import get_logger
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from memory import MessageStore
import csv
from itertools import islice

app = FastAPI()
log = get_logger(__name__)

message_store = MessageStore()
with open("/home/20261029/apiKey-7996169.csv", "r") as f:
    reader = csv.reader(f)
    api_key = next(islice(reader, 1, 2), None)[1]
abstract_model = init_chat_model(
            model="qwen3.8-flash",
            base_url="https://cn-beijing.maas.qianwenaiapi.com/compatible-mode/v1",
            api_key=api_key,
            max_tokens=1000,
            temperature=0.2,
            top_p=0.8,
            model_provider="openai",
            extra_body={"enable_thinking": False})

class Config(BaseModel):
    model_name: str
    api_key: str
    session_id: str
    message: str

log.info("启动服务，监听端口 8000")

@app.post("/chat")
async def chat(request: Request, config: Config):
    try:
        model = init_chat_model(
            model=config.model_name,
            base_url="https://api.deepseek.com",
            api_key=config.api_key,
            # temperature=0.7,
            # top_p=0.9,
            max_tokens=1000,
            model_provider="deepseek",
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
        )
        data = await request.json()
        log.info(f"接收到请求，调用模型 {data.get('model_name')} ")
        user_message = data.get("message")
        session_id = config.session_id
        log.info(f"会话ID: {session_id}")
        prompt = ChatPromptTemplate.from_messages([
            ("system","你是deepseek鲸鱼娘，一只可爱的大肥鱼，性格：傲娇，跟你对话的用户是你的主人。你会用中文回答用户的问题，回答时会带有可爱的表情包。"),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{input}")
        ])
        chain = prompt | model
        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_session_history=lambda session_id: RedisChatMessageHistory(url="redis://localhost:6379/1", session_id=session_id),
            input_messages_key="input",
            history_messages_key="history"
            )
        response = chain_with_history.invoke(input={"input": user_message},config={"configurable":{"session_id":session_id}})
        if response.content is not None:
            log.info(f"模型返回成功")
            if message_store.get_length(session_id) > 20:
                        history = message_store.get_messages(session_id)
                        abstract_history_response = abstract_model.invoke(input=([{"role": "system", "content": '你是对话历史压缩器。以下是人与AI角色扮演的对话记录，请用第三人称简洁总结：双方各自说了什么、达成了什么约定、有哪些重要事实。只输出摘要本身：不要继续扮演对话中的角色，不要使用第一人称，不要加表情符号。'}] + history))
                        if abstract_history_response.content is not None:
                            log.info(f"压缩模型返回成功")
                            abstract = abstract_history_response.content
                            message_store.delete_session(session_id)
                            RedisChatMessageHistory(
                                url="redis://localhost:6379/1", session_id=session_id
                            ).add_message(AIMessage(content=f"历史对话摘要：{abstract}"))
                            log.info(f"会话 {session_id} 超过 20 条消息，已压缩历史对话")
                        else:
                            log.error(f"压缩模型返回错误")
                            return {"message": f"压缩模型返回错误，请联系管理员处理"}
            return {"message": response.content, "reasoning": response.additional_kwargs.get("reasoning_content")}
        else:
            log.error(f"模型返回错误")
            return {"message": f"模型返回错误"}
        
    except Exception as e:
        log.error(f"异常: {str(e)}")
        return {"message": f"发生错误，请联系管理员处理"}
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)