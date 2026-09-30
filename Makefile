.PHONY: test serve about

test:
	uv run pytest
	node --test apps/web/explain.test.mjs

serve:
	uv run --package poludzku-pismo pismo serve

about:
	uv run --package poludzku-pismo pismo about
