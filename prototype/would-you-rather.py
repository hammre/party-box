#/usr/bin/env python3
# requires autobahn, Twisted

import json
import random
from twisted.internet.endpoints import clientFromString
from autobahn.twisted.websocket import WebSocketClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol

from messages import CreateRoomMessage, StaticMessage, SimpleMultiChoiceQuestion

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.pending_question = None
        self.answer_id = None


class WouldYouRather:
    required_capabilities = ['multi-choice', 'static-message']
    def __init__(self):
        self.players = {}
        self.vip_player = None
        self.room = None
        self.game_started = False

    def connect(self, endpoint, wsurl):
        from twisted.internet import reactor
        wsfactory = ClientFactory(wsurl)
        wsfactory.game = self 
        wsclient = clientFromString(reactor, endpoint)
        wsclient.connect(wsfactory)

    def onOpen(self):
        create_room = CreateRoomMessage(self.required_capabilities, "Would You Rather 0.1", "WouldYouRather?")
        self.connection.sendMessage( create_room.encode() )
        print("Connection to broker established")

    def onMessage(self, payload, isBinary):
        print("Received message: {}".format(payload))
        if isBinary:
            return

        msgdata = json.loads(payload.decode('utf-8'))
        command = msgdata.get('command', None)
        if command == 'create-room-response':
            self.room_created(msgdata)
        elif command == 'participant-status':
            self.onParticipantStatus(msgdata)
        elif command == 'participant-message':
            self.onParticipantMessage(msgdata)
        else:
            print("Command {} unhandled".format(command))

    def onParticipantMessage(self, msg):
        source = msg.get("from", None)
        if 'question-identifier' in msg:
            if not self.game_started:
                if msg['question-identifier'] == self.start_game_button[0] and \
                   msg['selection']['answer-identifier'] == self.start_game_button[1]:
                    
                       self.start_game()
                else:
                    print("Got message that answers a question not asked?")
            else:
                answer_id = msg.get('selection', {}).get("answer-identifier", None)
                if source in self.players:
                    self.players[source].answer_id = answer_id
                self.wait_message(source)
        else:
            print("Got non answer message.")

    def room_created(self, msgdata):
        if msgdata['status'] == 0:
            self.room = msgdata['room-code']
            print("Room code for game is {}".format(msgdata['room-code']))
        else:
            print("Create room error: {} {}".format(msgdata['status'], msgdata['status-message']))

    def vip_message(self, name):
        m = SimpleMultiChoiceQuestion(self.room, name, "You are the VIP, press the button to get started.", ["Start the game."])
        self.start_game_button = (m.question_id, m.choices[0]['answer-identifier'])
        self.connection.sendMessage( m.encode() )

    def wait_message(self, name):
        m = StaticMessage(self.room, name, "Hold tight while we wait for <em>everyone</em>.", is_html=True)
        self.connection.sendMessage( m.encode() )

    def onParticipantStatus(self, msgdata):
        name = msgdata.get('participant-name', None)
        status = msgdata.get('presence', None)
        if not self.game_started:
            if status == "connected":
                print("{} joined game.".format(name))
                if name not in self.players:
                    self.players[name] = Player(name)
                if len(self.players) == 1:
                    self.vip_player = name
                    self.vip_message(name)
                else:
                    self.wait_message(name)

            elif status == "disconnected":
                print("{} left game.".format(name))
                if name in self.players:
                    del self.players[name]
        else:
            if name not in self.players:
                print("Ignoring status for non-player {} {}".format(name, status))
            else:
                if status == "disconnected":
                    print("Player {} disconnected".format(name))
                else:
                    print("Player {} rejoined".format(name))

    def start_game(self):
        self.game_started = True
        print("Game starting.")
        for player in self.players:
            m = StaticMessage(self.room, player, "Starting game...")
            self.connection.sendMessage( m.encode() )
        self.player_turns = iter(self.players)

        self.connection.factory.reactor.callLater(10, self.start_round)

    def start_round(self):
        try:
            self.current_player = next(self.player_turns)
            self.current_question = self.get_question()
            print("{} is the current judge.".format(self.current_player))
            q = self.judge_question(self.current_player, self.current_question)
            for player in self.players:
                if player != self.current_player:
                    self.rest_question(player, q)
            self.connection.factory.reactor.callLater(30, self.collect_answers)
        except StopIteration:
            print("Game is over, all players have had a round.")
            self.end_game()

    def end_game(self):
        for player in self.players:
            score = self.players[player].score
            m = StaticMessage(self.room, player, "Your score is {}".format(score))
            self.connection.sendMessage(m.encode())
        self.game_started = False

    def judge_question(self, player, question):
        m = SimpleMultiChoiceQuestion(self.room, player, "Would you rather?", 
                question['choices'])
        self.players[player].pending_question = m
        self.connection.sendMessage( m.encode() )
        return m

    def rest_question(self, player, m):
        m.prompt = "What would {} rather?".format(self.current_player)
        m.participant = player
        self.players[player].pending_question = m
        self.connection.sendMessage( m.encode() )

    def collect_answers(self):
        print("Times up to answer, examining answers.")
        correct_answer = self.players[self.current_player].answer_id
        answer_label = None
        for c in self.players[self.current_player].pending_question.choices:
            if c['answer-identifier'] == correct_answer:
                answer_label = c['label']
                break
        else:
            answer_label = "Answer not found!?"

        correct = []
        incorrect = []
        for player in self.players:
            if player == self.current_player:
                continue
            
            if self.players[player].answer_id == correct_answer:
                print("{} guessed correctly!".format(player))
                correct.append(player)
                self.players[player].score += 1
            else:
                print("{} guessed incorrectly!".format(player))
                incorrect.append(player)

        print("The correct answer was {} ({}), {} got it right, {} got it wrong.".format(
            answer_label, correct_answer, correct, incorrect))

        correct_msg = '<span style="color:green">Correct!</span> {} got it right, {} got it wrong.'.format(correct, incorrect)
        incorrect_msg = '<span style="color:red">Incorrect!</span> {} got it right, {} got it wrong.'.format(correct, incorrect)
        judge_msg = 'You were the judge this round. {} got it right, {} got it wrong.'.format(correct, incorrect)

        for player in correct:
            self.connection.sendMessage( StaticMessage(self.room, player, correct_msg, is_html=True).encode() )

        for player in incorrect:
            self.connection.sendMessage( StaticMessage(self.room, player, incorrect_msg, is_html=True).encode() )

        self.connection.sendMessage( StaticMessage(self.room, self.current_player, judge_msg).encode() )

        self.connection.factory.reactor.callLater(15, self.start_round)

    def get_question(self):
        with open('questions.json', 'rb') as qfile:
            qs = json.load(qfile)
            return random.choice(qs)


class Client(WebSocketClientProtocol):
    def onOpen(self):
        self.game = self.factory.game
        self.game.connection = self
        self.game.onOpen()

    def onMessage(self, payload, isBinary):
        self.game.onMessage(payload, isBinary)

class ClientFactory(WebSocketClientFactory):
    protocol = Client

def main():
    import sys
    from twisted.python import log
    from autobahn.twisted.choosereactor import install_reactor

    reactor = install_reactor()

    log.startLogging(sys.stdout)

    game = WouldYouRather()
    game.connect("tcp:game.enimihil.net:80", "ws://game.enimihil.net/ws")

    reactor.run()

if __name__=='__main__':
    main()
