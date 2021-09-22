.PHONY: build

build:
	docker build -t mamercad/alpine-ansible:latest .

login:
	docker login --username mamercad --password "$(cat ~/.vault-pass)"

push:
	docker push mamercad/alpine-ansible:latest
