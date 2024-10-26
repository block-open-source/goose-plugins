import pytest
from unittest.mock import MagicMock, Mock, patch
from exchange import Exchange, Text
from exchange.content import Content
from typing import Any
from goose_plugins.toolkits.critical_systems_thinking import CriticalSystemsThinking


@pytest.fixture
def critical_systems_thinking() -> CriticalSystemsThinking:
    notifier: MagicMock = MagicMock()
    toolkit: CriticalSystemsThinking = CriticalSystemsThinking(notifier=notifier)
    toolkit.exchange_view = Mock()
    toolkit.exchange_view.processor = Mock()
    toolkit.exchange_view.processor.messages = []
    return toolkit


def test_message_content_with_text(critical_systems_thinking: CriticalSystemsThinking) -> None:
    text: Text = Text("test message")
    result: Text = critical_systems_thinking.message_content(text)

    assert result == text


def test_message_content_with_other_content(critical_systems_thinking: CriticalSystemsThinking) -> None:
    content: Mock = Mock(spec=Content)
    content.__str__ = Mock(return_value="test content")

    result: Text = critical_systems_thinking.message_content(content)

    assert isinstance(result, Text)
    assert result.text == "test content"


@patch("goose_plugins.toolkits.critical_systems_thinking.serper_search")
def test_search(mock_serper_search: Mock, critical_systems_thinking: CriticalSystemsThinking) -> None:
    expected_response: str = '{"results": []}'
    mock_serper_search.return_value = expected_response
    query: str = "test query"

    result: str = critical_systems_thinking.search(query)

    assert result == expected_response
    mock_serper_search.assert_called_once_with(query)
    critical_systems_thinking.notifier.status.assert_called_once_with("searching...")


@patch("goose_plugins.toolkits.critical_systems_thinking.AnthropicProvider")
def test_analyze_request(mock_provider_class: Mock, critical_systems_thinking: CriticalSystemsThinking) -> None:
    expected_analysis: str = "Analysis result"
    mock_provider: Mock = Mock()
    mock_provider_class.from_env.return_value = mock_provider
    mock_response: Mock = Mock()
    mock_response.content = [Text(expected_analysis)]

    with patch("goose_plugins.toolkits.critical_systems_thinking.ask_an_ai") as mock_ask:
        mock_ask.return_value = mock_response
        statement: str = "test statement"

        result: str = critical_systems_thinking.analyze_request(statement)

        assert result == expected_analysis
        critical_systems_thinking.notifier.status.assert_called_with("analyzing request...")

        call_args: Any = mock_ask.call_args
        assert statement in call_args[1]["input"]
        assert isinstance(call_args[1]["exchange"], Exchange)


@patch("goose_plugins.toolkits.critical_systems_thinking.get_web_page_content")
@patch("goose_plugins.toolkits.critical_systems_thinking.AnthropicProvider")
def test_review_web_page(
    mock_provider_class: Mock, mock_get_content: Mock, critical_systems_thinking: CriticalSystemsThinking
) -> None:
    web_content: str = "Sample web content"
    expected_summary: str = "Page summary"
    url: str = "http://example.com"

    mock_get_content.return_value = web_content
    mock_provider: Mock = Mock()
    mock_provider_class.from_env.return_value = mock_provider
    mock_response: Mock = Mock()
    mock_response.content = [Text(expected_summary)]

    with patch("goose_plugins.toolkits.critical_systems_thinking.ask_an_ai") as mock_ask:
        mock_ask.return_value = mock_response

        result: str = critical_systems_thinking.review_web_page(url)

        assert result == expected_summary
        mock_get_content.assert_called_once_with(url)
        critical_systems_thinking.notifier.status.assert_any_call(f"fetching content from {url}")
        critical_systems_thinking.notifier.status.assert_any_call(f"reviewing content: {web_content[:50]}...")


@patch("goose_plugins.toolkits.critical_systems_thinking.get_web_page_content")
def test_review_web_page_error(mock_get_content: Mock, critical_systems_thinking: CriticalSystemsThinking) -> None:
    error_message: str = "Failed to fetch"
    url: str = "http://example.com"
    mock_get_content.side_effect = Exception(error_message)

    result: str = critical_systems_thinking.review_web_page(url)

    assert result == f"Error: {error_message}"
    mock_get_content.assert_called_once_with(url)


@patch("goose_plugins.toolkits.critical_systems_thinking.AnthropicProvider")
def test_consider_solutions(mock_provider_class: Mock, critical_systems_thinking: CriticalSystemsThinking) -> None:
    expected_solution: str = "Solution analysis"
    mock_provider: Mock = Mock()
    mock_provider_class.from_env.return_value = mock_provider
    mock_response: Mock = Mock()
    mock_response.content = [Text(expected_solution)]

    with patch("goose_plugins.toolkits.critical_systems_thinking.ask_an_ai") as mock_ask:
        mock_ask.return_value = mock_response
        statement: str = "test problem"

        result: str = critical_systems_thinking.consider_solutions(statement)

        assert result == expected_solution
        critical_systems_thinking.notifier.status.assert_called_with("considering solutions...")

        call_args: Any = mock_ask.call_args
        assert statement in call_args[1]["input"]
        assert isinstance(call_args[1]["exchange"], Exchange)


def test_system_prompt(critical_systems_thinking: CriticalSystemsThinking) -> None:
    expected_prompt: str = "System prompt content"

    with patch("exchange.Message.load") as mock_load:
        mock_message: Mock = Mock()
        mock_message.text = expected_prompt
        mock_load.return_value = mock_message

        result: str = critical_systems_thinking.system_prompt()

        assert result == expected_prompt
        mock_load.assert_called_once_with("prompts/critical_systems_thinking.jinja")


if __name__ == "__main__":
    pytest.main(["-v"])
