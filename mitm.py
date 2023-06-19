import json
import mitmproxy.http
import socketio

# initialising socket io client
sio = socketio.Client()

# Debug output for connection to server
@sio.event
def connect():
    print('SocketIO connected')

# Debug output for disconnection from server
@sio.event
def disconnect():
    print('SocketIO disconnected')

# connecting to IDS server
sio.connect('http://localhost:5000/hi')

# handling proxied request
def request(flow: mitmproxy.http.HTTPFlow):
    data = {
        'method': flow.request.method,
        'url': flow.request.pretty_url,
        'headers': dict(flow.request.headers),
        'content': flow.request.content.decode(),
    }
    sio.emit('request', data, namespace="/") # sending request to IDS

# Telling MITMProxy API to disconnect from socketio server upon exit
def done():
    sio.disconnect()
