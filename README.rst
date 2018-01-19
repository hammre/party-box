=========
Party Box
=========

A framework for building mobile web + big screen (TV) party games.  In the
style of Jackbox Party Pack games, or other games with similar mechanics.

Architecture
============

There are three major pieces to this framework, each representing a different
piece of interacting software; combined, they form the full game experience.

Client
    This is the mobile web component, it interacts with the broker to present a
    player-specific UI for interacting with the game.
Broker
    This is a public web server, hosting the client assets, and a websocket
    endpoint for brokering communications between that client and the game.
Game
    This is the software that runs on the big screen, it talks to the broker
    using a websocket connection to establish the game and communicate with the
    players via their devices.

Nothing prevents the Game and Broker from being co-located, but the function of
the Broker is ideally suited for a public Internet web server, where the Game
is ideally suited to run on a computer or game console attached to a
television.

Broker
======

As the Broker represents the central point of rendezvous and communication
between the Game and the Clients, we will start with explaining what functions
the broker provides itself.

The broker exposes a web socket server, which both the Game and Clients
establish connections to.  The messages exchanges are JSON objects. (Framing
TBD, does Websockets provide message framing?)

The details of the messages are documented in JSON-Schema in the schemas/
directory.

The Broker manages "Rooms", which are used to establish communication between a
group of Clients and the Game.  Clients are identified by a "Participant Name",
and Rooms by a "Room Code".

When a request to create a Room is received, the Broker generates a Room code
and returns it to the requestor (usually this is done by the Game).

Clients will then receive (out of band) the Room Code and can connect to the
Broker and join the Room using that code.

Participant status is communicated to the creator of a Room (the Game) via
asynchronous events.

The Broker is responsible for removing state about the Room when no participants
are left.

Participants leave by disconnecting from the websocket, there is no difference
between a 'graceful' disconnect and an ungraceful one.

For messages that receive a response, a status code of 0 is considered a
success, any other value is an error, with the status-message optionally
populated with a human-friendly (developer-friendly) error message.

It is an error to join a room that does not exist.

Capabilities are strings presented by the Game to the Broker, and by the Broker
to the Clients.  These represent the needed support of messages not defined by
the Broker itself between the Client and the Game in order to work correctly.

It is usually the case that the Broker knows what Capabilities are supported by
the Client that it serves, and this allows the Broker to reject an attempt to
create a room with capabilities that Clients will not understand.

There are two types of general-purpose messages for communication between the
Game and the Clients: a broadcast and a participant-directed message.

The broadcast is a request to send that exact message to all participants that
are connected to the Room.  The Broker will add a single "from" property to the
message indicating the participant name that generated the message. If a
participant submits a message that includes a "from" property, it must match the
particpant name.

A participant message is a reques to send that exact message to the specific
participant in the Room.  The Broker will add a single "from" property to the
message indicating the participant name that generated the message. If a
participant submits a message that includes a "from" property, it must match the
particpant name.

When a participant joins a Room, the current set of participants will be
communicated by the Broker generating a status of "connected" for each
participant towards the joining participant.

Creating a room successfully implies a successful joining to the Room as well.
(And the generation of participant status messages, though creating a room
should not be able to return a room-code that is already in use.)

If a Game becomes disconnected, the Game can reconnect to the Room in exactly
the same way as any participant could, using the same participant name as used
in the create-room command. (Brokers are suggested to validate this
reconnection as the creator of a Room with some care, potentially only allowing
this from the same transport layer address as originally connected)
