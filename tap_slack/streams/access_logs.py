from tap_slack.streams.base import BaseStream
import singer
import datetime
import time

LOGGER = singer.get_logger()  # noqa


class AccessLogsStream(BaseStream):
    API_METHOD = 'team_accessLogs'
    TABLE = 'access_logs'
    KEY_PROPERTIES = ['user_id', 'ip', 'user_agent']
    TIMEOUT = 3

    def response_key(self):
        return 'logins'

    def get_params(self):
        return {
            "count": 100,
            "page": 1,
            "before": "now"
        }

    def transform_record(self, record):
        transformed = super().transform_record(record)

        # Anonymize IPs by dropping the last octet
        if self.config.get('anonymize_ips', True):
            ip = transformed.get('ip', '')
            parts = ip.split('.')
            parts[-1] = 'x'
            transformed['ip'] = '.'.join(parts)

        return transformed

    def sync_paginated(self, params):
        table = self.TABLE

        params = self.get_params()

        oldest, latest = self.get_lookback()
        stop_at_timestamp = oldest

        # This endpoint unfortunately doesn't not allow us to query _forward_ in time,
        # only backwards. So, we must just start at today and work our way backwards
        # until we reach some stopping point. This endpoint orders access logs by date_first,
        # which is the _first_ time that a user was seen at a given ip/user-agent. Since we're
        # looking backwards in time, there might be some very old records whose date_last is
        # is continually updated, but we unfortunately are not able to capture this informatation
        # with the current capabilities of the Slack API. When using the data replicated by this
        # stream, be sure to remember that the date_first will be accurate but the date_last will
        # be misleading an incorrect. For perfect information, set the "lookback_days" value to some
        # very large number of days to capture all historical access log information

        while True:
            response = self.client.make_request(self.API_METHOD, params, self.TIMEOUT)
            transformed = self.get_stream_data(response)

            if len(transformed) == 0:
                LOGGER.info(f"No more data available - stopping at {params['before']}")
                break
            else:
                min_date_first = transformed[-1]['date_first']

            with singer.metrics.record_counter(endpoint=table) as counter:
                singer.write_records(table, transformed)
                counter.increment(len(transformed))

            params['before'] = min_date_first

            remaining = response.get('paging', {}).get('pages')
            LOGGER.info(f"{remaining} pages remaining")

            if min_date_first < stop_at_timestamp:
                LOGGER.info(f"Exceeded stop_at_timestamp - stopping at {params['before']}")
                break
            else:
                self.log_progress(oldest, min_date_first)