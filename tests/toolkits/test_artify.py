import os
import pytest
import requests
import unittest
from unittest.mock import patch, MagicMock
from goose_plugins.toolkits.artify import VincentVanCode


@pytest.fixture
def artify() -> VincentVanCode:
    notifier = MagicMock()
    return VincentVanCode(notifier=notifier)


def test_vincent_van_code(artify: VincentVanCode) -> None:
    code_snippet = "print('Hello, World!')"
    with patch.object(VincentVanCode, "create_image", return_value="image: path/to/image.png") as mock_create_image:
        result = artify.vincent_van_code(code_snippet, "test_image.png")
        mock_create_image.assert_called_once_with(code_snippet, "test_image.png")
        assert result == "image: path/to/image.png"


def test_create_image_success(artify: VincentVanCode) -> None:
    prompt = "A sunset over a mountain range"
    image_name = "sunset.png"
    fake_response = MagicMock()
    fake_response.json.return_value = {"data": [{"url": "http://example.com/image.png"}]}
    fake_image_response = MagicMock()
    fake_image_response.content = b"fake_image_data"

    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake_api_key"}), patch(
        "httpx.Client.post", return_value=fake_response
    ) as mock_post, patch("requests.get", return_value=fake_image_response) as mock_get, patch(
        "builtins.open", new_callable=unittest.mock.mock_open
    ) as mock_file, patch("os.makedirs", return_value=None) as mock_makedirs, patch.object(
        artify.notifier, "log"
    ) as mock_log:
        result = artify.create_image(prompt, image_name)

        mock_post.assert_called_once()
        mock_get.assert_called_once_with("http://example.com/image.png")
        mock_file.assert_called_once_with(os.path.join(os.getcwd(), "tmp", image_name), "wb")
        mock_makedirs.assert_called_once_with(os.path.join(os.getcwd(), "tmp"), exist_ok=True)

        assert result == os.path.join(os.getcwd(), "tmp", image_name)
        mock_log.assert_any_call(f"Image {result} saved successfully. Size: {len(fake_image_response.content)} bytes")


def test_create_image_no_api_key(artify: VincentVanCode) -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is not set"):
            artify.create_image("A sunset over a mountain range", "sunset.png")


def test_create_image_api_error(artify: VincentVanCode) -> None:
    prompt = "A sunset over a mountain range"
    image_name = "sunset.png"
    fake_response = MagicMock()
    fake_response.json.return_value = {"data": [{"url": "http://example.com/image.png"}]}
    fake_image_response = MagicMock()
    fake_image_response.content = b"fake_image_data"

    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake_api_key"}), patch(
        "httpx.Client.post", return_value=fake_response
    ) as mock_post, patch("requests.get", return_value=fake_image_response) as mock_get, patch(
        "builtins.open", new_callable=unittest.mock.mock_open
    ) as mock_file, patch("os.makedirs", return_value=None) as mock_makedirs, patch.object(
        artify.notifier, "log"
    ) as mock_log:
        mock_file.return_value.write.side_effect = requests.HTTPError("Error")

        with pytest.raises(requests.HTTPError, match="Error"):
            artify.create_image(prompt, image_name)

        mock_post.assert_called_once()
        mock_get.assert_called_once_with("http://example.com/image.png")
        mock_makedirs.assert_called_once_with(os.path.join(os.getcwd(), "tmp"), exist_ok=True)
        mock_log.assert_any_call("Error occurred: Error")
        mock_log.assert_any_call("Raising exception")
