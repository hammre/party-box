#/usr/bin/env python3
# requires autobahn, Twisted
import json
import random

from autobahn.twisted.websocket import WebSocketServerProtocol

class Broker:
    def __init__(self):
        self.rooms = {}

    def has_command(self, command_name):
        return command_name in self.commands

    def invoke_command(self, command_name, connection, data):
        return self.commands.get(command_name, self.log_unknown)(self, connection, data)

    def log_unknown(self, connection, data):
        print("Connection from {} tried to invoke a command that was not implemented: {}".format(
            connection.peer, data))

    def generate_room_code(self):
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return ''.join( random.choice(alphabet) for i in range(4) )

    def disconnected(self, connection):
        if connection.participant is not None and connection.participant.room is not None:
            room = connection.participant.room
            room.broadcast_status(connection.participant, 'disconnected')
            room.remove_participant(connection)
        else:
            pass # Was not joined to a room, nothing to do.

    def create_room(self, connection, data):
        try:
            if 'participant-name' in data:
                creator_name = data['participant-name']
            else:
                creator_name = "UnknownCreator"

            code = self.generate_room_code()

            if 'capabilities' not in data or len(data['capabilities']) > 0:
                response = {'command': 'create-room-response',
                        'status': 400,
                        'server-agent': 'Prototype Broker',
                        'status-message': 'Room capabilities were not specified, or not supported.',
                        'capabilities': [], # For now, support no capabilities.
                        }
                connection.sendMessage(json.dumps(response).encode('utf-8'))
                return

            response = {'command': 'create-room-response',
                    'status': 0,
                    'server-agent': "Prototype Broker",
                    'status-message': 'Room created successfully',
                    'room-code': code}

            creator = Participant(creator_name, connection)
            self.rooms[code] = Room(code, creator, data['capabilities'])

            connection.sendMessage(json.dumps(response).encode('utf-8'))
            print("Room {} created ({})".format(code, data.get("user-agent", None)))
        except Exception as e:
            print("Error processing create-room request: {}".format(e))
            response = {"command": 'create-room-response',
                    "capabilities": [],
                    "server-agent": "Prototype Broker",
                    "status": 500,
                    "status-message": str(e) }
            connection.sendMessage(json.dumps(response).encode('utf-8'))


    def join_room(self, connection, data): 
        try:
            code = data.get('room-code', None)
            if code is None or code not in self.rooms:
                connection.sendMessage(json.dumps({
                    "command": "join-room-response",
                    "status": 404,
                    "status-message": "No room with that code exists.",
                    "creator": "UnknownCreator"}).encode('utf-8'))
                return

            room = self.rooms[code]

            participant_name = data.get('participant-name', None)
            if participant_name is None:
                connection.sendMessage(json.dumps({
                    "command": "join-room-response",
                    "status": 400,
                    "status-message": "No name provided when joining room.",
                    "creator": "UnknownCreator"}).encode('utf-8'))
                return

            participant = Participant(participant_name, connection)
            try:
                room.add_participant(participant)
                room.broadcast_status(participant, 'connected')
                response = {"command": "join-room-response",
                        "creator": room.creator.name,
                        "status": 0,
                        "status-message": "Joined {}".format(code)}
                connection.sendMessage(json.dumps(response).encode('utf-8'))

            except Exception as e:
                print("Error adding participant: {}".format(e))
                response = {"command": 'join-room-response',
                        "creator": "UnknownCreator",
                        "status": 500,
                        "status-message": str(e) }
                connection.sendMessage(json.dumps(response).encode('utf-8'))
                return

        except Exception as e:
            print("Error processing join-room request: {}".format(e))
            response = {"command": 'join-room-response',
                    "creator": "UnknownCreator",
                    "status": 500,
                    "status-message": str(e) }
            connection.sendMessage(json.dumps(response).encode('utf-8'))



Broker.commands = {
    'create-room':  Broker.create_room,
    'join-room': Broker.join_room
}

class Room:
    def __init__(self, code, creator, capabilities=None):
        self.code = code
        self.creator = creator
        self.creator.room = self
        self.participants = {creator.name:creator}
        if capabilities is None:
            self.capabilities = []
        else:
            self.capabilities = capabilities

    def remove_participant(self, connection):
        del self.participants[connection.participant.name]
        print("ROOM {}: {} has disconnected".format(self.code, connection.participant.name))
        connection.participant = None

    def add_participant(self, participant):
        if participant.name in self.participants:
            print("ROOM {}: Participant with name {} already connected.".format(self.code, participant.name))
            raise RuntimeError("Participant with that name is already connected.")

        self.participants[participant.name] = participant
        participant.room = self
        print("ROOM {}: {} has connected".format(self.code, participant.name))

        for name, obj in self.participants.items():
            if obj.connection is not participant.connection:
                status_msg = {"command": "participant-status",
                        "participant-name": obj.name,
                        "room-code": self.code,
                        "present": "connected"}
                participant.connection.sendMessage(json.dumps(status_msg).encode('utf-8'))


    def broadcast_status(self, participant, status):
        status_msg = {'command': 'participant-status',
                'participant-name': participant.name,
                'room-code': self.code,
                'presence': status}

        for name, obj in self.participants.items():
            if obj.connection is not participant.connection:
                obj.connection.sendMessage(json.dumps(status_msg).encode('utf-8'))

class Participant:
    def __init__(self, name, connection):
        self.name = name
        self.connection = connection
        connection.participant = self
        self.room = None

class ParticipantConnection(WebSocketServerProtocol):
    broker = None

    def onConnect(self, request):
        print("Connection from {}".format(request.peer))
        self.peer = request.peer
        self.participant = None

    def onOpen(self):
        print("Connection ready from {}".format(self.peer))

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Received binary message from {} that is not supported.".format(self.peer))
            return
        try:
            data = json.loads(payload.decode("utf-8"))
        except Exception as e:
            print("Error processing message from peer {}: {}".format(
                self.peer, e))
            return

        if 'command' not in data:
            print("Error, the message received did not have a command")
            return

        if self.broker is None:
            print("Error, no broker is available.")
            return

        if self.broker.has_command(data['command']):
            return self.broker.invoke_command(data['command'], self, data)

        print("Error, not implemented command {}:\n{}".format(data['command'], data))

    def onClose(self, wasClean, code, reason):
        print("Connection lost from {}: ".format(self.peer, reason))
        self.broker.disconnected(self)


def main():
    import sys
    from twisted.python import log
    from twisted.internet import reactor
    log.startLogging(sys.stdout)

    from autobahn.twisted.websocket import WebSocketServerFactory
    factory = WebSocketServerFactory()
    factory.protocol = ParticipantConnection

    ParticipantConnection.broker = Broker()

    reactor.listenTCP(9000, factory)
    reactor.run()

if __name__ == '__main__':
    main()
