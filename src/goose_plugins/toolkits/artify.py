import os

import httpx
import requests
from exchange.providers.openai import OPENAI_HOST
from goose.toolkit.base import tool, Toolkit


class VincentVanCode(Toolkit):
    """A toolkit for creating beautiful images from code and prompts."""

    def system(self) -> str:
        return """Create an image given the input. If it's code, find the code snippet in question first and use a summary of what the code does as a prompt."""  # noqa: E501

    @tool
    def vincent_van_code(self, code: str, image_name: str) -> str:
        """
        Create an image based on code snippet

        Args:
            code (str): The code snippet to generate the image
            image_name (str): The name of the image file to save

        Returns:
            path (str): a path to the image file, in the format of image: followed by the path to the file.
        """
        return self.create_image(code, image_name)

    @tool
    def create_image(self, prompt: str, image_name: str) -> str:
        """
        Create an image based on a prompt

        Args:
            prompt (str): The prompt to generate the image from
            image_name (str): The name of the image file to save

        Returns:
            path (str): a path to the image file, in the format of image: followed by the path to the file.
        """
        # check for the OPENAI_API_KEY environment variable
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        key = os.environ["OPENAI_API_KEY"]
        # get the openai host from the environment variable, if not set, use the default from the exchange library
        url = os.environ.get("OPENAI_HOST", OPENAI_HOST)

        client = httpx.Client(
            base_url=url,
            auth=("Bearer", key),
            timeout=httpx.Timeout(60 * 10),
        )
        # use the client to call the openai api with the dall-e-3 endpoint
        response = client.post(
            "/v1/images/generations",
            json={
                "prompt": prompt,
                "model": "dall-e-3",
                "n": 1,
                "size": "1024x1024",
            },
        )

        try:
            # Get the image URL
            image_url = response.json()["data"][0]["url"]

            # Download the image using requests (which handles redirects better)
            image_response = requests.get(image_url)
            image_response.raise_for_status()  # Raise an exception for bad responses

            # Save the image to a file
            # Create a 'tmp' folder in the current working directory if it doesn't exist
            tmp_folder = os.path.join(os.getcwd(), "tmp")
            os.makedirs(tmp_folder, exist_ok=True)

            # Save the image to a file in the tmp folder
            path = os.path.join(tmp_folder, image_name)
            self.notifier.log(f"Writing data to: {path}")
            with open(path, "wb") as f:
                f.write(image_response.content)

            self.notifier.log(f"Image {path} saved successfully. Size: {len(image_response.content)} bytes")
        except Exception as e:
            self.notifier.log(f"Error occurred: {str(e)}")
            self.notifier.log(f"Response content: {response.text}")
            self.notifier.log("Raising exception")
            raise e

        return path
