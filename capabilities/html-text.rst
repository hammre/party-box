========================
The html-text Capability
========================

This capability, identified by the ``html-text`` string, represents the
ability of a Client to render text using HTML.  This allows the specification of
text prompts, or other messages intended for display to the participant by the
client as HTML fragments.

These fragments SHOULD NOT include dynamic behaviors, embedded Javascript, or
other complex features available in modern browsers.  Basic styling and
formatting is the intended usage, though it is up to Client implementations,
along with Game implementations to restrict usage to a subset. (Not specified
here.)

The messages which are sent are not specific to this capability, but any message
with properties defined as "string"-type, may have this capability mixed into it
by including the ``html-text-content`` property with an array of the property
names whose contents are HTML text rather than plain text.  A JSON Schema of
this property can be found in ``html-text.json``.
