import time
import slack
import singer
import singer.metrics

LOGGER = singer.get_logger()


class SlackClient:

    def __init__(self, config):
        self.config = config
        self.client = slack.WebClient(
            token=self.config['token'],
            headers={"User-Agent": self.config.get('user_agent')}
        )

    def make_request(self, method_name, params):
        time.sleep(2)
        LOGGER.info("Making request to {} ({})".format(method_name, params))

        method = getattr(self.client, method_name)
        response = method(**params)

        if response.status_code != 200:
            LOGGER.info(response.data)
            raise RuntimeError(response)

        return response.data
