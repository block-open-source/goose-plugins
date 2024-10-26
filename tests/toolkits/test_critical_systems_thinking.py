import pytest
from goose_plugins.toolkits.critical_systems_thinking import CriticalSystemsThinking
from unittest.mock import MagicMock, Mock


@pytest.fixture
def critical_systems_thinking() -> CriticalSystemsThinking:
    notifier = MagicMock()
    toolkit = CriticalSystemsThinking(notifier=notifier)
    toolkit.exchange_view = Mock()
    toolkit.exchange_view.processor = Mock()
    toolkit.exchange_view.processor.messages = []
    return toolkit


def test_check_status(critical_systems_thinking: CriticalSystemsThinking) -> None:
    result = critical_systems_thinking.check_status()

    assert "OK" == result


if __name__ == "__main__":
    pytest.main()
