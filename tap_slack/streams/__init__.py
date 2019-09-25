
from tap_slack.streams.users import UsersStream
from tap_slack.streams.channels import ChannelsStream
from tap_slack.streams.conversations import ConversationsStream


AVAILABLE_STREAMS = [
   UsersStream,
   ChannelsStream,
   ConversationsStream,
]

__all__ = [
   'UsersStream',
   'ChannelsStream',
   'ConversationsStream',
]
