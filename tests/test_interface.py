# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=no-self-use,protected-access
from unittest.mock import MagicMock

from hcoopmeetbotlogic.interface import Context, Message


class TestContext:
    def test_constructor(self):
        get_topic = MagicMock()
        set_topic = MagicMock()
        send_reply = MagicMock()
        send_message = MagicMock
        context = Context(get_topic, set_topic, send_reply, send_message)
        assert context.set_topic is set_topic
        assert context.send_reply is send_reply
        assert context.send_message is send_message


class TestMessage:
    def test_constructor(self):
        timestamp = MagicMock()
        message = Message("id", timestamp, "nick", "channel", "network", "payload", "topic", ["one", "two"])
        assert message.id == "id"
        assert message.timestamp is timestamp
        assert message.nick == "nick"
        assert message.channel == "channel"
        assert message.network == "network"
        assert message.payload == "payload"
        assert message.topic == "topic"
        assert message.channel_nicks == ["one", "two"]
