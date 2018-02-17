=============================
The static-message Capability
=============================

This capability, identified by the ``static-message`` string, represents the
ability of a Client to display a simple static message.

The Game would normally generate this message, indicating to the participant
that something is happening and they need only wait. (For the start of the game,
after they have answered a question that round, etc.)

The message follows the JSON Schema outlined in ``static-message.json``.

Messages intended to match this capability are identified by the
``static-message-text`` property.
