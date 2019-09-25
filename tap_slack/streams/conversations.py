
from tap_slack.streams.base import BaseStream
from tap_slack.cache import stream_cache

import singer
import datetime
import time

LOGGER = singer.get_logger()  # noqa


class ConversationsStream(BaseStream):
    API_METHOD = 'conversations_history'
    TABLE = 'messages'
    KEY_PROPERTIES = ['ts']

    def response_key(self):
        return 'messages'

    def get_params(self, channel_id, oldest, latest):
        return {
            "limit": 100,
            "channel": channel_id,
            "oldest": oldest,
            "latest": latest,
        }

    def sync_data(self):
        table = self.TABLE
        LOGGER.info('Syncing data for {}'.format(table))

        for channel in stream_cache['channels']:
            if channel['is_archived']:
                LOGGER.info("Skipping channel '{}' : it is archived".format(channel['name']))
                continue
            else:
                LOGGER.info("Syncing conversation history for '{}'".format(channel['name']))

            self.sync_channel(channel)

        return self.state

    def sync_channel(self, channel):
        latest_date = datetime.date.today()
        one_month = datetime.timedelta(days=30)
        oldest_date = latest_date - one_month

        oldest = int(time.mktime(oldest_date.timetuple()))
        latest = int(time.mktime(latest_date.timetuple()))

        return self.sync_for_interval(channel['id'], oldest, latest)

    def sync_for_interval(self, channel_id, oldest, latest):
        table = self.TABLE
        params = self.get_params(channel_id, oldest, latest)

        while True:
            response = self.client.make_request(self.API_METHOD, params)
            transformed = self.get_stream_data(response, channel_id)

            with singer.metrics.record_counter(endpoint=table) as counter:
                singer.write_records(table, transformed)
                counter.increment(len(transformed))

            meta = response.get('response_metadata', {})
            next_cursor = meta.get('next_cursor', '')

            if len(next_cursor) > 0:
                params['cursor'] = next_cursor
            else:
                break

    def get_stream_data(self, response, channel_id):
        transformed = []

        for record in response[self.response_key()]:
            record['channel_id'] = channel_id
            record = self.transform_record(record) 
            transformed.append(record)

        return transformed
