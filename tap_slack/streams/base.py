import singer
import singer.utils
import singer.metrics

from tap_slack.state import incorporate, save_state

from tap_framework.streams import BaseStream as base
from tap_slack.cache import stream_cache

import datetime
import time


LOGGER = singer.get_logger()


class BaseStream(base):
    KEY_PROPERTIES = ['id']
    CACHE = False
    TIMEOUT = 2
    DEFAULT_LOOKBACK = 30

    def get_lookback(self):
        lookback = self.config.get('lookback', {}).get(self.TABLE, self.DEFAULT_LOOKBACK)
        LOGGER.info(f"Lookback window is set to {lookback} days for stream {self.TABLE}")
        latest_date = datetime.date.today()
        time_delta = datetime.timedelta(days=lookback)
        oldest_date = latest_date - time_delta

        oldest = int(time.mktime(oldest_date.timetuple()))
        latest = int(time.mktime(latest_date.timetuple()))

        return oldest, latest

    def log_progress(self, oldest, latest):
        end_date = datetime.datetime.fromtimestamp(oldest)
        end_date_s = end_date.strftime('%Y-%m-%d')
        cur_date = datetime.datetime.fromtimestamp(latest)
        cur_date_s = cur_date.strftime('%Y-%m-%d')
        delta = (cur_date - end_date).days


        LOGGER.info(
            f"From={cur_date_s} until={end_date_s}. {delta} days remaining to sync"
        )

    def get_params(self):
        return {}

    def sync_paginated(self, params):
        table = self.TABLE

        while True:
            response = self.client.make_request(self.API_METHOD, params, self.TIMEOUT)
            transformed = self.get_stream_data(response)

            with singer.metrics.record_counter(endpoint=table) as counter:
                singer.write_records(table, transformed)
                counter.increment(len(transformed))

            if self.CACHE:
                stream_cache[table].extend(transformed)

            meta = response.get('response_metadata', {})
            next_cursor = meta.get('next_cursor', '')

            if len(next_cursor) > 0:
                params['cursor'] = next_cursor
            else:
                break

    def sync_data(self):
        table = self.TABLE
        LOGGER.info('Syncing data for {}'.format(table))
        params = self.get_params()
        self.sync_paginated(params)

        return self.state

    def get_stream_data(self, response):
        transformed = []

        for record in response[self.response_key()]:
            record = self.transform_record(record) 
            transformed.append(record)

        return transformed
