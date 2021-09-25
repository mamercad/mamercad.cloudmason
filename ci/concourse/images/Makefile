DOCKER_HUB_USERNAME := mamercad
DOCKER_HUB_PASSWORD := "$(shell cat ~/.docker-hub-password)"

IMAGE_NAME := $(DOCKER_HUB_USERNAME)/alpine-ansible
IMAGE_TAG := latest

.PHONY: docker-login docker-build docker-push docker-run
.DEFAULT_GOAL := docker-push

docker-login:
	@echo $(DOCKER_HUB_PASSWORD) | docker login --username $(DOCKER_HUB_USERNAME) --password-stdin

docker-build: docker-login
	@docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

docker-push: docker-build
	@docker push $(IMAGE_NAME):$(IMAGE_TAG)

docker-run:
	@docker run --rm -it $(IMAGE_NAME):$(IMAGE_TAG) ash
