import aio_pika
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

app = FastAPI()

class Activity(BaseModel):
    id: int
    description: str

@app.post("/activities/")
async def create_activity(activity: Activity):
    # Here you would typically save the activity to your database
    # For this example, we'll just print it
    print(f"Activity created: {activity}")
    # Send a notification to the STOMP broker
    await send_stomp_message(activity)
    return activity

async def send_stomp_message(activity):
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    channel = await connection.channel()

    exchange = await channel.declare_exchange("activities", aio_pika.ExchangeType.FANOUT)
    message = aio_pika.Message(body=json.dumps(activity.dict()).encode())

    await exchange.publish(message, routing_key="")
    await connection.close()
@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if necessary
            print(f"Received message: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
