#!/usr/bin/env python

import asyncio
import json
import logging
import websockets

logging.basicConfig()

STATE = {"value": 0}

# Contains each room name as a key + the appertaining
# sessions as a value
ROOMS = {
}

# Contains a mapping from session ==> user
USER_SESSIONS = {
}

# Contains the session as a key and the room name as a value
SESSION_ROOMS = {}

def state_event():
    return json.dumps({"type": "state", **STATE})

def message_event(message, user_name):
    return json.dumps({"type": 3, "message": message, "from": user_name})

def users_event(room_name):
    return json.dumps({"type": 2, "users": [USER_SESSIONS[session] for session in ROOMS[room_name]]})

def available_rooms_event():
    return json.dumps({"type": 1, "rooms": [key for key in ROOMS.keys()]})

def add_user_to_room(user_name, room_name, session):
    if room_name in ROOMS:
        # Add new session to room
        ROOMS[room_name].add(session)
        # Add mapping between session and room
        SESSION_ROOMS[session] = room_name
        # Add mapping between session and username
        USER_SESSIONS[session] = user_name

def remove_user(session):
    room = SESSION_ROOMS[session]
    # Remove session from room
    ROOMS[room].remove(session)
    # Remove mapping between session and name
    del USER_SESSIONS[session]
    # Remove mapping between session and room
    del SESSION_ROOMS[session]
    return room

def send_message_to_room(room_name, message):
    print("Sending message '" + message + "' to room " + room_name)
    websockets.broadcast(ROOMS[room_name], message)

async def handler(websocket, path):
    try:
        # at first, we add each user to the default room
        await websocket.send(available_rooms_event())
        # Manage state changes
        async for message in websocket:
            data = json.loads(message)
            # User Join message
            if data["type"] == 1:
                payload = data["data"]
                user_name = payload["userName"]
                room_name = payload["roomName"]

                # room wasn't present --> create + send update
                if not room_name in ROOMS:
                    # create new room
                    ROOMS[room_name] = set()
                    await websocket.send(available_rooms_event())

                # Add new user to room
                add_user_to_room(user_name, room_name, websocket)
                send_message_to_room(room_name, users_event(room_name)) # Broadcast join in this room
                pass
            elif data["type"] == 2:
                payload = data["data"]
                message = payload["message"]
                send_message_to_room(SESSION_ROOMS[websocket], message_event(message, USER_SESSIONS[websocket]))
                pass
    finally:
        # Unregister user
        room_name = remove_user(websocket)
        send_message_to_room(room_name, users_event(room_name)) # Broadcast join in this room


async def main():
    async with websockets.serve(handler, "0.0.0.0", 6789):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
