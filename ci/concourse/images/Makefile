.PHONY: login build push

.DEFAULT_GOAL := push

login:
	docker login --username mamercad --password "$(lpass show 'Homelab\Ansible/Vault' --password)"

build:
	docker build -t mamercad/alpine-ansible:latest .

push: build
	docker push mamercad/alpine-ansible:latest
