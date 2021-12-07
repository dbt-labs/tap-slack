
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
    TIMEOUT = 2

    def response_key(self):
        return 'messages'

    def get_params(self, channel_id, oldest, latest):
        return {
            "limit": 1000,
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
        return self.sync_for_interval(channel['id'])

    def fetch_replies(self, channel_id, root_msg_ts, i, total):
        replies = []
        params = {
            "channel": channel_id,
            "ts": root_msg_ts,
            "cursor": '',
            "limit": 1000
        }

        while True:
            response = self.client.make_request('conversations_replies', params, self.TIMEOUT)
            LOGGER.info(f"  - Found {len(response['messages'])} replies for thread {i+1} of {total}")
            replies.extend(response['messages'])

            meta = response.get('response_metadata', {})
            next_cursor = meta.get('next_cursor', '')

            if len(next_cursor) > 0:
                params['cursor'] = next_cursor
            else:
                break

        return replies

    def sync_for_interval(self, channel_id):
        table = self.TABLE

        oldest, latest = self.get_lookback()
        params = self.get_params(channel_id, oldest, latest)

        while True:
            response = self.client.make_request(self.API_METHOD, params, self.TIMEOUT)

            messages = response[self.response_key()]
            total = len(messages)
            for i, message in enumerate(messages):
                reply_count = message.get('reply_count', 0)
                if message.get('reply_count', 0) > 0 and 'ts' in message:
                    message['threaded_replies'] = self.fetch_replies(channel_id, message['ts'], i, total)
                else:
                    message['threaded_replies'] = []

            transformed = self.get_stream_data(response, channel_id)

            with singer.metrics.record_counter(endpoint=table) as counter:
                singer.write_records(table, transformed)
                counter.increment(len(transformed))

            meta = response.get('response_metadata', {})
            next_cursor = meta.get('next_cursor', '')

            if len(next_cursor) > 0 and len(messages) > 0:
                last_message_ts = messages[-1]['ts']
                params['cursor'] = next_cursor
                self.log_progress(oldest, float(last_message_ts))
            else:
                break

    def get_stream_data(self, response, channel_id):
        transformed = []

        for record in response[self.response_key()]:
            record['channel_id'] = channel_id
            record = self.transform_record(record) 
            transformed.append(record)

        return transformed
