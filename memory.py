import json
import redis



class MessageStore:
    def __init__(self, db=1):
        self.r = redis.Redis(host='localhost', port=6379, db=db, decode_responses=True)

    def get_length(self, session_id):
        key = self.r.keys(f"message_store:{session_id}")[0]
        return len(self.r.lrange(key, 0, -1))

    def get_messages(self, session_id):
        messages = []
        key = self.r.keys(f"message_store:{session_id}")[0]
        for item in reversed(self.r.lrange(key, 0, -1)):
            js = json.loads(item)
            messages.append({"role": js["type"] if js["type"] == "human" else "assistant", "content": js["data"]["content"]})
        return messages

    def delete_session(self, session_id):
        keys = self.r.keys(f"message_store:{session_id}")
        if keys:
            self.r.delete(*keys)
            return True
        return False

if __name__ == "__main__":
    m = MessageStore()
    print(m.get_length("001"))
    print(m.get_messages("001"))

