
from tap_slack.streams.users import UsersStream
from tap_slack.streams.channels import ChannelsStream
from tap_slack.streams.conversations import ConversationsStream
from tap_slack.streams.access_logs import AccessLogsStream


AVAILABLE_STREAMS = [
   UsersStream,
   ChannelsStream,
   ConversationsStream,
   AccessLogsStream,
]

__all__ = [
   'UsersStream',
   'ChannelsStream',
   'ConversationsStream',
   'AccessLogsStream',
]
