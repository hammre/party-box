import json

import random
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

class CreateRoomMessage:
    def __init__(self, capabilities, user_agent=None, name=None):
        self.capabilities = capabilities
        self.user_agent = user_agent
        self.name = name

    def encode(self):
        msg = {"command": "create-room"}
        msg['capabilities'] = self.capabilities
        if self.user_agent is not None:
            msg['user-agent'] = self.user_agent
        if self.name is not None:
            msg['participant-name'] = self.name

        return json.dumps(msg, ensure_ascii=False).encode('utf-8')

class CreateRoomResponseSuccess:
    def __init__(self, room_code, capabilities, server_agent=None):
        self.room_code = room_code
        self.capabilities = capabilities
        self.server_agent = server_agent

    def encode(self):
        msg = {"command": "create-room-response"}
        msg['room-code'] = self.room_code
        msg['capabilities'] = self.capabilities
        if self.server_agent is not None:
            msg['server-agent'] = self.server_agent
        msg['status'] = 0
        msg['status-message'] = "Room {} created successfully".format(self.room_code)

        return json.dumps(msg, ensure_ascii=False).encode('utf-8')

class CreateRoomResponseFailure:
    def __init__(self, status, msg, capabilities, server_agent=None):
        self.status = status
        self.msg = msg
        self.capabilities = capabilities
        self.server_agent = server_agent

    def encode(self):
        msg = {"command": "create-room-response"}
        msg['capabilities'] = self.capabilities
        if self.server_agent is not None:
            msg['server-agent'] = self.server_agent
        msg['status'] = self.status
        msg['status-message'] = self.msg

        return json.dumps(msg, ensure_ascii=False).encode('utf-8')

class JoinRoomMessage:
    def __init__(self, room_code, name, user_agent=None, capabilities=None):
        self.room_code = room_code
        self.name = name
        self.capabilities = capabilities
        self.user_agent = user_agent

    def encode(self):
        msg = {"command": "join-room"}
        msg['room-code'] = self.room_code
        msg['participant-name'] = self.name
        if self.capabilities is not None:
            msg['capabilities'] = self.capabilities
        if self.user_agent is not None:
            msg['user-agent'] = self.user_agent

        return json.dumps(msg, ensure_ascii=False).encode('utf-8')

class JoinRoomResponseSuccess:
    def __init__(self, creator, capabilities=None, creator_agent=None, server_agent=None):
        self.creator = creator
        self.capabilities = capabilities
        self.creator_agent = creator_agent
        self.server_agent = server_agent

    def encode(self):
        msg = {"command": "join-room-response"}
        msg['creator'] = self.creator
        if self.capabilities is not None:
            msg['capabilities'] = self.capabilities
        if self.server_agent is not None:
            msg['server-agent'] = self.server_agent
        if self.creator_agent is not None:
            msg['creator-agent'] = self.creator_agent
        msg['status'] = 0
        msg['status-message'] = "Joined"

        return json.dumps(msg, ensure_ascii=False).encode('utf-8')
    
class JoinRoomResponseFailure:
    def __init__(self, status, msg, creator=None, capabilities=None, creator_agent=None, server_agent=None):
        self.status = status
        self.msg = msg
        self.creator = creator
        self.capabilities = capabilities
        self.creator_agent = creator_agent
        self.server_agent = server_agent

    def encode(self):
        msg = {"command": "join-room-response"}
        if self.creator is None:
            msg['creator'] = "Unknown"
        else:
            msg['creator'] = self.creator
        if self.capabilities is not None:
            msg['capabilities'] = self.capabilities
        if self.server_agent is not None:
            msg['server-agent'] = self.server_agent
        if self.creator_agent is not None:
            msg['creator-agent'] = self.creator_agent
        msg['status'] = self.status
        msg['status-message'] = self.msg

        return json.dumps(msg, ensure_ascii=False).encode('utf-8')

class ParticipantStatusMessage:
    def __init__(self, room, name, status):
        self.room = room
        self.name = name
        self.status = status


    def encode(self):
        msg = {"command": "join-room-response"}
        msg['room-code'] = self.room
        msg['participant-name'] = self.name
        msg['presence'] = self.status
        return json.dumps(msg, ensure_ascii=False).encode('utf-8')

class SimpleMultiChoiceQuestion:
    def __init__(self, room, participant, prompt, choices):
        self.room = room
        self.participant = participant
        self.prompt = prompt
        self.choices = self.make_choices(choices)
        self.question_id = ''.join(random.choice(alphabet) for i in range(8))

    def make_choices(self, choices):
        r = []
        for c in choices:
            r.append({"answer-identifier": ''.join(random.choice(alphabet) for i in range(4)),
                "label":c})
        return r

    def encode(self):
        msg = {"command": "participant-message"}
        msg['question-identifier'] = self.question_id
        msg['prompt'] = self.prompt
        msg['choices'] = self.choices
        msg['room-code'] = self.room
        msg['participant-name'] = self.participant
        return json.dumps(msg, ensure_ascii=False).encode('utf-8')

class SimpleMultiChoiceAnswer:
    def __init__(self, room, participant, qid, choice):
        self.room = room
        self.participant = participant
        self.question_id = qid
        self.choice = choice

    def encode(self):
        msg = {"command": "participant-message"}
        msg['question-identifier'] = self.question_id
        msg['selection'] = self.choice
        msg['room-code'] = self.room
        msg['participant-name'] = self.participant
        return json.dumps(msg, ensure_ascii=False).encode('utf-8')

class StaticMessage:
    def __init__(self, room, participant, msg):
        self.room = room
        self.participant = participant
        self.msg = msg

    def encode(self):
        msg = {"command":"participant-message"}
        msg['room-code'] = self.room
        msg['participant-name'] = self.participant
        msg['static-message'] = self.msg
        return json.dumps(msg, ensure_ascii=False).encode("utf-8")
