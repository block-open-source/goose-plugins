test *FLAGS:
  uv run pytest tests -m "not integration" {{FLAGS}}

coverage *FLAGS:
  uv run coverage run -m pytest tests -m "not integration" {{FLAGS}}
  uv run coverage report
  uv run coverage lcov -o lcov.info