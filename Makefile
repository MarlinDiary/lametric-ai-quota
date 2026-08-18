.PHONY: icons test verify docker-build container-verify

icons:
	python3 scripts/generate_icons.py

test: icons
	PYTHONPATH=src python3 -m unittest discover -s tests -v

verify:
	./scripts/verify.sh

docker-build:
	docker build -t lametric-ai-quota:local .

container-verify: docker-build
	./scripts/verify_container.sh
