
from tap_slack.streams.base import BaseStream
import singer

LOGGER = singer.get_logger()  # noqa


class UsersStream(BaseStream):
    API_METHOD = 'users_list'
    TABLE = 'users'
    TIMEOUT = 10
    KEY_PROPERTIES = ['id']

    def response_key(self):
        return 'members'
