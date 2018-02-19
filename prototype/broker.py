#/usr/bin/env python3
# requires autobahn, Twisted, jinja2
import json
import random
from urllib.parse import urlunsplit, quote_plus

from twisted.web.resource import Resource
from twisted.web.util import redirectTo

from autobahn.twisted.websocket import WebSocketServerProtocol

from jinja2 import Template

from messages import JoinRoomResponseSuccess, \
                     JoinRoomResponseFailure, \
                     CreateRoomResponseSuccess, \
                     CreateRoomResponseFailure, \
                     ParticipantStatusMessage

class Broker:
    server_agent = "Prototype Broker"
    client_capabilities = ['multi-choice', 'static-message']
    broker_capabilities = []

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
        code = None
        while code is  None or code in self.rooms:
            code = ''.join( random.choice(alphabet) for i in range(4) )
        return code

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
                creator_name = "RoomCreator"

            code = self.generate_room_code()

            if 'capabilities' not in data:
                response = CreateRoomResponseFailure(400, 
                    "Room capabilities were not specified.", 
                    self.client_capabilities, server_agent=self.server_agent)
                connection.sendMessage(response.encode())
                return

            for cap in data['capabilities']:
                if cap not in self.client_capabilities and cap not in self.broker_capabilities:
                    response = CreateRoomResponseFailure(405,
                            "Room capability {} not supported by clients (or broker).".format(cap),
                            self.client_capabilities, server_agent=self.server_agent)
                    connection.sendMessage(response.encode())
                    return

            response = CreateRoomResponseSuccess(code, data['capabilities'], server_agent=self.server_agent)

            creator = Participant(creator_name, connection)
            self.rooms[code] = Room(code, creator, data['capabilities'])

            connection.sendMessage(response.encode())
            print("Room {} created by \"{}\" ({}) capabilities: {}".format(
                code, creator_name, data.get("user-agent", None), data['capabilities']))
        except Exception as e:
            print("Error processing create-room request: {}".format(e))
            response = CreateRoomResponseFailure(500, str(e), self.client_capabilities, server_agent=self.server_agent)
            connection.sendMessage(response.encode())


    def join_room(self, connection, data): 
        try:
            code = data.get('room-code', None)
            if code is None or code not in self.rooms:
                connection.sendMessage(JoinRoomResponseFailure(404,
                    "No room with that code exists").encode())
                return

            room = self.rooms[code]

            participant_name = data.get('participant-name', None)
            if participant_name is None:
                connection.sendMessage(JoinRoomResponseFailure(400,
                    "No name provided when joining room.").encode())
                return

            capabilities = data.get('capabilities', None)
            if capabilities is not None:
                for cap in room.capabilities:
                    if cap not in capabilities:
                        connection.sendMessage(JoinRoomResponseFailure(405,
                            "This client does not support capability {}, refuse to join room {}".format(
                                cap, code), server_agent=self.server_agent, capabilities=room.capabilities).encode())
                        return


            participant = Participant(participant_name, connection)
            try:
                room.add_participant(participant)
                room.broadcast_status(participant, 'connected')
                
                response = JoinRoomResponseSuccess(room.creator.name,
                        capabilities=room.capabilities, server_agent=self.server_agent)                
                connection.sendMessage(response.encode())

            except Exception as e:
                print("Error adding participant: {}".format(e))
                response = JoinRoomResponseFailure(500, str(e), server_agent=self.server_agent)
                connection.sendMessage(response.encode())
                return

        except Exception as e:
            print("Error processing join-room request: {}".format(e))
            response = JoinRoomResponseFailure(500, str(e), server_agent=self.server_agent)
            connection.sendMessage(response.encode())

    def participant_message(self, connection, data):
        try:
            code = data['room-code']
            if code not in self.rooms:
                print("Error, room {} does not exist".format(code))
                return

            room = self.rooms[code]

            sender = None
            recipient = None
            for p in room.participants.values():
                if p.connection is connection:
                    sender = p
                elif p.name == data['participant-name']:
                    recipient = p

            if sender is None:
                print("Error, room {} participant with connection {} could not be mapped to a name.".format(connection))
                return
            if recipient is None:
                print("Error, room {} could not find participants {} for message delivery".format(code, data['participant-name']))
                return

            if 'from' in data:
                if sender.name != data['from']:
                    print("Error, sender {} in room {} tried to impersonate {}".format(sender.name, code, data['from']))
                    return
            else:
                data['from'] = sender.name

            recipient.connection.sendMessage( 
                    json.dumps(data, ensure_ascii=False).encode('utf-8')
            )

        except Exception as e:
            print("Error processing participant-message: {}".format(e))



Broker.commands = {
    'create-room':  Broker.create_room,
    'join-room': Broker.join_room,
    'participant-message': Broker.participant_message,
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
                        "presence": "connected"}
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

def make_error_redirect(msg, request):
    url = "/?message={}".format(quote_plus(msg))
    code = request.args.get(b"code", [None])[0]
    if code:
        url += "&code={}".format(quote_plus(code))
    nick = request.args.get(b'nick', [None])[0]
    if nick:
        url += "&nick={}".format(quote_plus(nick))

    return redirectTo(url.encode('utf-8'), request)

class RoomJoinResource(Resource):
    isLeaf = True

    def render_POST(self, request):
        code = request.args.get(b"code", [None])[0]
        nick = request.args.get(b"nick", [None])[0]
        if code is None or not code:
            print("No room code supplied")
            return make_error_redirect("No room code supplied!", request)
        else:
            code = code.decode("utf-8").strip()
        if nick is None or not nick:
            print("No nickname supplied")
            return make_error_redirect("No nickname supplied!", request)
        else:
            nick = nick.decode("utf-8").strip()

        if not nick or not code:
            print("Nickname or code was empty string")
            return make_error_redirect("Nickname or room code were empty!", request)

        code = code.upper()
        if len(nick) > 20:
            nick = nick[:20]

        if code not in ParticipantConnection.broker.rooms:
            return make_error_redirect("Room {} does not exist".format(code), request)

        #room_url = "/room#code:{code};nick:{nick}".format(code=code, nick=nick)
        room_url = ('', '', '/room', '', 'code:{code};nick:{nick}'.format(code=quote_plus(code), nick=quote_plus(nick)))
        print("room_url {}".format(room_url))
        url = urlunsplit(room_url)
        print("url {}".format(url))
        return redirectTo(url.encode('ascii'), request)


class RootPage(Resource):
    isLeaf = True

    def render_GET(self, request):
        request.responseHeaders.addRawHeader(b"Content-Type", b"text/html; charset=utf-8")
        room_prefill = request.args.get(b'code', [None])[0]

        if room_prefill is not None and room_prefill:
            room_prefill = room_prefill.decode('utf-8')
        else:
            room_prefil = None

        message = request.args.get(b'message', [None])[0]
        if message is not None and message:
            message = message.decode('utf-8')
        else:
            message = None

        nick = request.args.get(b'nick', [None])[0]
        if nick is not None and nick:
            nick = nick.decode("utf-8")
        else:
            nick = None

        with open('index.html', 'rb') as idxfile:
            page = Template(idxfile.read().decode('utf-8'))
        return page.render(room_prefill=room_prefill, message=message, nick=nick).encode('utf-8')
        

    def getChild(self, name, request):
        if name == '':
            return self
        else:
            return Resource.getChild(self, name, request)


def main():
    import sys
    from twisted.python import log
    from twisted.internet import reactor
    from twisted.web.server import Site
    from twisted.web.static import File
    from autobahn.twisted.resource import WebSocketResource
    from autobahn.twisted.websocket import WebSocketServerFactory

    log.startLogging(sys.stdout)

    ParticipantConnection.broker = Broker()

    factory = WebSocketServerFactory()
    factory.protocol = ParticipantConnection

    ws_resource = WebSocketResource(factory)

    root = Resource()
    root.putChild(b"", RootPage())
    root.putChild(b"ws", ws_resource)
    root.putChild(b"join", RoomJoinResource())
    root.putChild(b"room", File('room'))

    site = Site(root)

    reactor.listenTCP(9000, site)
    reactor.run()

if __name__ == '__main__':
    main()
