#!/usr/bin/env python3
# requires python websocket-client

import websocket
from pprint import pprint
import json
import random
from messages import CreateRoomMessage, SimpleMultiChoiceQuestion, StaticMessage, alphabet

def gen_id(length):
    return ''.join(random.choice(alphabet) for i in range(length))

class SurveyQuestion:
    def __init__(self, prompt, choices):
        self.prompt = prompt
        self.choices = [(gen_id(4), c) for c in  choices]
        self.qid = gen_id(8) 
        self.answers = {}

    def sendto(self, room, name):
        msg = {"command": "participant-message"}
        msg['question-identifier'] = self.qid
        msg['prompt'] = self.prompt
        msg['choices'] = [ {"answer-identifier": c[0], "label": c[1]} for c in self.choices ]
        msg['room-code'] = room
        msg['participant-name'] = name
        return json.dumps(msg, ensure_ascii=False).encode("utf-8")

    def answered(self, msg):
        if 'question-identifier' not in msg:
            print("{} sent message that did not answer the question.".format(msg.get('from', None)))
            return

        aid = msg.get("selection", {}).get("answer-identifier", None)
        answer = 'Unknown'
        for i, m in self.choices:
            if aid == i:
                answer = m
        if aid is not None:
            print("{} answered {} ({})".format(msg.get('from', None), answer, aid))

        self.answers[msg.get('from', None)] = (aid, answer)

    def results_response(self, room, name):
        msg = {"command": "participant-message"}
        msg['room-code'] = room
        msg['participant-name'] = name
        msg['html-text-content'] = ['static-message']
        results = []
        for answerer, answer in self.answers.items():
            results.append("{} answered {}".format(answerer, answer[1]))
        msg['static-message'] = '<br>'.join(results)
        return json.dumps(msg, ensure_ascii=False).encode("utf-8")


s = websocket.WebSocket()
s.connect("ws://localhost:9000/ws")
m = CreateRoomMessage(["multi-choice", "static-message"], name="Quizmaster", user_agent="Multi-Choice prototype Game")
s.send(m.encode())
question = SurveyQuestion("What is your choice of meal?", 
    ["Pizza", "Burgers", "Fish Fry", "Full Diner Breakfast"])
while True:
    try:
        msg = json.loads(s.recv())
        if msg.get('command', None) == 'participant-status':
            if msg.get('presence', None) == 'connected':
                m = question.sendto(room, msg.get('participant-name', None))
                s.send(m)
        elif msg.get('command', None) == 'participant-message':
            pprint(msg)
            question.answered(msg)
            m = question.results_response(room, msg.get('from', None))
            s.send(m)
        elif msg.get('command', None) == 'create-room-response':
            if msg['status'] != 0:
                print("Error creating room: {}".format(msg))
                break
            room = msg['room-code']
            print("Created room {}".format(room))
        else:
            print("Unknown message")
            pprint(msg)
    except KeyboardInterrupt:
        break
s.close()
