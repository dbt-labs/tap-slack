import time
import slack_sdk
import singer
import singer.metrics
import ssl

LOGGER = singer.get_logger()

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class SlackClient:

    def __init__(self, config):
        self.config = config
        self.client = slack_sdk.WebClient(
            token=self.config['token'],
            headers={"User-Agent": self.config.get('user_agent')},
            ssl = ssl_context
        )

    def make_request(self, method_name, params, timeout, attempt=1):
        LOGGER.info(" - Sleeping for {} seconds".format(timeout))
        time.sleep(timeout)
        LOGGER.info(" - Making request to {} ({})".format(method_name, params))

        method = getattr(self.client, method_name)
        response = method(**params)

        if attempt > 5:
            raise RuntimeError("Too many 429s, exiting!")
        elif response.status_code == 429:
            LOGGER.info("429 error, retrying after delay")
            time.sleep(timeout * 10)
            return self.make_request(method_name, params, timeout, attempt + 1)
        elif response.status_code != 200:
            LOGGER.info(response.data)
            raise RuntimeError(response)

        return response.data
