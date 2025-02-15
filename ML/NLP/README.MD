AGENT:
Принимает 4 параметры:
message: str
name: str
age: int
id: (сделайте на сеанс uuid4 и в этом сеансе используйте его)

запрос делается так:

{
    "input": {
        "messages": `messages`,
        "name": `name`,
        "age": `age`
    },
    "config": {
        "configurable": {
            "checkpoint_id": "1", 
            "checkpoint_ns": "",  
            "thread_id": `id` 
                    }
    },
    "kwargs": {}
}
url = "http://localhost:8000/graph/invoke"
headers = {'Content-Type': 'application/json'}
requests.post(url, headers=headers, data=json.dumps(payload))



для получения ответа - 
response.json()['output']['messages'][-1].content