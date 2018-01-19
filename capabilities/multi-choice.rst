===========================
The multi-choice Capability
===========================

This capability, identified by the ``multi-choice`` string, represents the
ability of a Client to present a set of simple text choices, along with a
prompt, and accept the submissions of the choice.

The Game would normally generate the message indicating to the participant what
their choices are.

This would follow the JSON Schema outlined in ``multi-choice-question.json``

The Client would present the choices to the player, allow a selection, which
SHOULD be made exactly once, and not repeated. (The Game is free to interpret
repeated selections as duplicates, or to discard all but the first, as it sees
fit to do.)

The Client then generates a message to the ``from`` in the message it received
following the ``multi-choice-answer.json`` schema.
