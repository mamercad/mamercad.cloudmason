.PHONY: login build push

.DEFAULT_GOAL := push

login:
	docker login quay.io

build:
	ansible-builder build --tag quay.io/mamercad/ansible-ee:0.1.0 --container-runtime docker

push: build
	docker push quay.io/mamercad/ansible-ee:0.1.0
