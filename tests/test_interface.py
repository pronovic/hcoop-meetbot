# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=no-self-use,protected-access

from unittest.mock import MagicMock

from hcoopmeetbotlogic.interface import Context, Message


class TestContext:
    def test_constructor(self):
        set_topic = MagicMock()
        send_reply = MagicMock()
        send_message = MagicMock
        context = Context(set_topic, send_reply, send_message)
        assert context.set_topic is set_topic
        assert context.send_reply is send_reply
        assert context.send_message is send_message


class TestMessage:
    def test_constructor(self):
        context = Message("nick", "channel", "network", "payload", "topic", ["one", "two"])
        assert context.nick == "nick"
        assert context.channel == "channel"
        assert context.network == "network"
        assert context.payload == "payload"
        assert context.topic == "topic"
        assert context.channel_nicks == ["one", "two"]
