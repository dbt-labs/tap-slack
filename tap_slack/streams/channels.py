from tap_slack.streams.base import BaseStream
import singer

LOGGER = singer.get_logger()  # noqa


class ChannelsStream(BaseStream):
    API_METHOD = 'conversations_list'
    TABLE = 'channels'
    KEY_PROPERTIES = ['id']
    CACHE = True

    def response_key(self):
        return 'channels'

    def get_params(self):
        return {
            "limit": 100,
            "types": 'public_channel'
        }
