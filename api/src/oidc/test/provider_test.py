import json
from typing import Any
from unittest import TestCase
from unittest.mock import patch

from oidc import provider


class FakeConfig:
    def __init__(self, **values: str) -> None:
        self.values = values

    def get(self, key: str, **kwargs: Any) -> str:
        return self.values.get(key, "")


def configured(**values: str) -> Any:
    return patch.object(provider.config, "config", FakeConfig(**values))


OUTLINE = dict(client_id="outline", client_secret="s1", redirect_uris=["https://wiki.example.com/auth/callback"])
GRAFANA = dict(client_id="grafana", client_secret="s2", redirect_uris=["https://grafana.example.com/login/generic"])


class Test(TestCase):
    def test_no_configuration_gives_no_clients(self) -> None:
        with configured():
            self.assertEqual({}, provider.get_configured_clients())
            self.assertIsNone(provider.validate_client_id("outline"))

    def test_multiple_clients_are_configured_independently(self) -> None:
        with configured(OIDC_CLIENTS=json.dumps([OUTLINE, GRAFANA])):
            clients = provider.get_configured_clients()
            self.assertEqual({"outline", "grafana"}, set(clients.keys()))

            outline = provider.validate_client_credentials("outline", "s1")
            assert outline is not None
            self.assertEqual(["https://wiki.example.com/auth/callback"], outline.redirect_uris)

            # A client may not authenticate with another client's secret.
            self.assertIsNone(provider.validate_client_credentials("outline", "s2"))
            self.assertIsNone(provider.validate_client_credentials("grafana", "s1"))
            self.assertIsNone(provider.validate_client_id("unknown"))

    def test_display_name_defaults_to_a_humanized_client_id(self) -> None:
        entry = dict(client_id="lovable_booking", client_secret="s1", redirect_uris=["https://a.example.com"])
        with configured(OIDC_CLIENTS=json.dumps([entry])):
            client = provider.validate_client_id("lovable_booking")
            assert client is not None
            self.assertEqual("Lovable Booking", client.display_name)

    def test_display_name_may_be_configured(self) -> None:
        entry = dict(
            client_id="lovable_booking",
            client_secret="s1",
            display_name="Makerspace Events",
            redirect_uris=["https://a.example.com"],
        )
        with configured(OIDC_CLIENTS=json.dumps([entry])):
            client = provider.validate_client_id("lovable_booking")
            assert client is not None
            self.assertEqual("Makerspace Events", client.display_name)

    def test_redirect_uris_may_be_a_comma_separated_string(self) -> None:
        entry = dict(
            client_id="outline", client_secret="s1", redirect_uris="https://a.example.com, https://b.example.com"
        )
        with configured(OIDC_CLIENTS=json.dumps([entry])):
            client = provider.validate_client_id("outline")
            assert client is not None
            self.assertEqual(["https://a.example.com", "https://b.example.com"], client.redirect_uris)

    def test_malformed_configuration_is_ignored(self) -> None:
        for raw in ["not json", "{}", '[{"client_id": "outline"}]', '[{"client_id": "outline", "client_secret": "s"}]']:
            with self.subTest(raw=raw), configured(OIDC_CLIENTS=raw):
                self.assertEqual({}, provider.get_configured_clients())

    def test_duplicate_client_id_keeps_the_first_definition(self) -> None:
        duplicate = dict(OUTLINE, client_secret="other")
        with configured(OIDC_CLIENTS=json.dumps([OUTLINE, duplicate])):
            self.assertEqual(1, len(provider.get_configured_clients()))
            self.assertIsNotNone(provider.validate_client_credentials("outline", "s1"))
            self.assertIsNone(provider.validate_client_credentials("outline", "other"))
