import stomp

class MyListener(stomp.ConnectionListener):
    def on_message(self, headers, message):
        print('Received message:', message)

# Connect to the broker
conn = stomp.Connection([('localhost', 4222)])
conn.set_listener('', MyListener())
conn.connect('user', 'password', wait=True)

# Send a message to the destination
conn.send(destination='/queue/test', body='Hello, STOMP!')

# Subscribe to the destination to receive messages
conn.subscribe(destination='/queue/test', id=1, ack='auto')

# Keep the connection alive to receive messages
import time
time.sleep(2)

# Disconnect
conn.disconnect()
