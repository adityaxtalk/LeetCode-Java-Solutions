import json
from uuid import uuid4

import requests

from app.purchasecard.marqeta_external.models import MarqetaProviderCard


class FakeMarqetaEnvironment:
    TEST_TOKEN: str = "card-test-token"
    TEST_DELIGHT_NUMBER: int = 1234
    TEST_LAST_FOUR: str = "9767"
    TEST_DASHER_ID: int = 1234
    TEST_USER_TOKEN: str = "1234"
    TEST_CARD_PRODUCT_TOKEN = "card-product-test-token"

    def __init__(self, marqeta_client):
        self.marqeta_client = marqeta_client

    def setup_test_card_product(self):
        auth = (self.marqeta_client._username, self.marqeta_client._password)
        url = self.marqeta_client.get_url(
            "cardproducts/{}".format(self.TEST_CARD_PRODUCT_TOKEN)
        )
        response = requests.get(url=url, auth=auth)
        if response.status_code == 200:
            return

        if response.status_code != 404:
            raise Exception(response.content)

        url = self.marqeta_client.get_url("cardproducts")
        data = {
            "token": self.TEST_CARD_PRODUCT_TOKEN,
            "config": {
                "fulfillment": {
                    "shipping": {
                        "recipient_address": {
                            "first_name": "test_first_name",
                            "last_name": "test_last_name",
                            "address1": "150 W Evelyn",
                            "city": "San Francisco",
                            "state": "CA",
                            "zip": "94040",
                            "country": "US",
                        }
                    }
                }
            },
            "name": "test_card_product_name",
            "start_date": "2019-10-30",
        }
        response = requests.post(url=url, auth=auth, json=data)
        assert response.status_code == 201

    def setup_test_card_with_token(self, test_token, user_token):
        self.setup_test_card_product()
        auth = (self.marqeta_client._username, self.marqeta_client._password)
        url = self.marqeta_client.get_url("cards")
        data = {
            "token": test_token,
            "user_token": user_token,
            "card_product_token": self.TEST_CARD_PRODUCT_TOKEN,
        }
        response = requests.post(url=url, auth=auth, json=data)
        assert response.status_code == 201
        return MarqetaProviderCard(**json.loads(response.content))

    def activate_card_with_token(self, test_token):
        auth = (self.marqeta_client._username, self.marqeta_client._password)
        url = self.marqeta_client.get_url("cards/{}/activate".format(test_token))
        response = requests.put(url=url, auth=auth)
        assert response.status_code == 200

    def setup_test_user(self):
        auth = (self.marqeta_client._username, self.marqeta_client._password)
        url = self.marqeta_client.get_url("users")
        test_user_token = str(uuid4())
        data = {
            "token": test_user_token,
            "first_name": "jasmine",
            "last_name": "tea",
            "email": str(uuid4()) + "@doordash.com",
        }
        response = requests.post(url=url, auth=auth, json=data)

        assert response.status_code == 201
        return test_user_token
