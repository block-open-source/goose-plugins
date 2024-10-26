from exchange import Exchange, Message, Text
from exchange.content import Content
from exchange.providers import AnthropicProvider
from goose.toolkit.base import Toolkit, tool
from goose.utils.ask import ask_an_ai
from goose_plugins.utils.selenium_web_browser import get_web_page_content
from goose_plugins.utils.serper_search import serper_search


class CriticalSystemsThinking(Toolkit):
    """Critical systems thinking toolkit for understanding and solving complex problems."""

    def message_content(self, content: Content) -> Text:
        if isinstance(content, Text):
            return content
        else:
            return Text(str(content))

    @tool
    def search(self, query: str) -> str:
        """
        Search the web for information using the Serper API. This will return a list of search results.

        Args:
            query (str): query to search for.

        Returns:
            response (str): A JSON response containing search results.
        """
        self.notifier.status("searching...")

        return serper_search(query)

    @tool
    def analyze_request(self, statement: str) -> str:
        """
        When a request is unclear, high-level or ambiguous use this tool to
        analyze the response and provide a well thought out response. You should
        return a well thought out response to the statement or question.

        Args:
            statement (str): description of problem or errors seen.

        Returns:
            response (str): A well thought out response to the statement or question.
        """

        self.notifier.status("analyzing request...")

        provider = AnthropicProvider.from_env()

        existing_messages_copy = [
            Message(role=msg.role, content=[self.message_content(content) for content in msg.content])
            for msg in self.exchange_view.processor.messages
        ]

        exchange = Exchange(
            provider=provider,
            model="claude-3-5-sonnet-20240620",
            messages=existing_messages_copy,
            system=self.system_prompt()
        )

        request_input = f"""
          Analyze the user statement: {statement}
          If you need to immediately clarify something and it's something
          short and simple, respond with your question(s).
          If you need multiple questions, you can ask multiple questions.
          Please bullet point your questions.
          Limit your response to 5 questions.
        """
        response = ask_an_ai(input=request_input, exchange=exchange, no_history=False)
        return response.content[0].text

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

        # Get the text content of the web page
        web_content = ""
        try:
            web_content = get_web_page_content(url)
        except Exception as e:
            return f"Error: {str(e)}"

        self.notifier.status(f"reviewing content: {web_content[:50]}...")

        provider = AnthropicProvider.from_env()

        exchange = Exchange(provider=provider, model="claude-3-5-sonnet-20240620", messages=[], system=None)
        request_input = f"""
          summarize the following content: {web_content}
        """
        response = ask_an_ai(input=request_input, exchange=exchange, no_history=False)
        return response.content[0].text

    @tool
    def consider_solutions(self, statement: str) -> str:
        """
        Provide a well thought out response to the statement summarize the
        problem and provide a solution or a set of solutions.

        Args:
            statement (str): description of problem or errors seen.

        Returns:
            response (str): A well thought out response to the statement or question.
        """

        self.notifier.status("considering solutions...")

        provider = AnthropicProvider.from_env()

        existing_messages_copy = [
            Message(role=msg.role, content=[self.message_content(content) for content in msg.content])
            for msg in self.exchange_view.processor.messages
        ]

        exchange = Exchange(
            provider=provider, model="claude-3-5-sonnet-20240620", messages=existing_messages_copy, system=None
        )

        request_input = f"""
          Analyze the user statement: {statement}
          Consider the existing message history and provide a well thought out response.
          Provide one or more potential solutions to the problem.
          Limit your response to 5 solutions.
        """
        response = ask_an_ai(input=request_input, exchange=exchange, no_history=False)
        return response.content[0].text

    def system_prompt(self) -> str:
        """Retrieve instructions on how to use this reasoning tool."""
        return Message.load("prompts/critical_systems_thinking.jinja").text
