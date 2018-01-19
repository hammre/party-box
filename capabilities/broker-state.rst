===========================
The broker-state Capability
===========================

This capability, identified by the ``broker-state`` string, represents the
ability of the Broker to record persistent state associated with a participant.

This state is communicated through the only ``participant-message`` commands
with a special ``broker-state`` property. 

Any such command seen by the broker will be stored.  Messages with equal values
for the ``broker-state`` property will overwrite the stored message in the
Broker.  These messages are participant and Room specific.

When the Broker responds to a ``join-room`` command, it will examine the set of
saved messages for the participant that has joined.  For each saved message it
will send that message to the participant.

Messages that are broadcast have no special handling, even if they have a
``broker-state`` property.  If a Broker supports this capability, but the Room
was not created with the capability, the Broker MUST not store the messages.

If a participant sends themselves a message with a ``broker-state`` property,
this instructs the Broker to store the message and send it to the participant if
that particpant reconnects.

Messages with distinct values for the ``broker-state`` property are stored for
as long as the Room is stored.  
