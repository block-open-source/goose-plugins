from goose.toolkit.base import tool
from goose_plugins.utils.serper_search import serper_search
from goose_plugins.utils.selenium_web_browser import get_web_page_content

class SearchTools:
    @tool
    def search(self, query: str) -> str:
        """
        Search the web for information using the Serper API.

        Args:
            query (str): query to search for.

        Returns:
            response (str): A JSON response containing search results.
        """
        self.notifier.status("searching...")
        return serper_search(query)

    @tool
    def review_web_page(self, url: str) -> str:
        """
        Review the content of a web page by providing a summary of the content.

        Args:
            url (str): URL of the web page to review.

        Returns:
            response (str): A summary of the content of the web page.
        """
        self.notifier.status(f"fetching content from {url}")
        try:
            web_content = get_web_page_content(url)
            self.notifier.status(f"reviewing content: {web_content[:50]}...")
            return self._ask_ai(f"summarize the following content: {web_content}")
        except Exception as e:
            return f"Error: {str(e)}"