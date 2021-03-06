.PHONY: fly-login fly-sync

fly-login:
	fly login -t cloudmason -c https://concourse.cloudmason.org

fly-sync:
	fly -t cloudmason sync

fly-targets:
	fly targets

fly-status:
	fly -t cloudmason status

fly-userinfo:
	fly -t cloudmason userinfo

fly-pipelines:
	fly -t cloudmason pipelines

fly-set-pipelines:
	fly -t cloudmason set-pipeline \
		--pipeline awx --config pipelines/awx.yml \
		--non-interactive
	fly -t cloudmason set-pipeline \
		--pipeline octodns --config pipelines/octodns.yml \
		--non-interactive
	fly -t cloudmason set-pipeline \
		--pipeline pre-commit --config pipelines/pre-commit.yml \
		--non-interactive
	fly -t cloudmason set-pipeline \
		--pipeline pull-request --config pipelines/pull-request.yml \
		--non-interactive

fly-test-pipelines:
	fly -t cloudmason validate-pipeline \
		--config pipelines/awx.yml
	fly -t cloudmason validate-pipeline \
		--config pipelines/octodns.yml

fly-unpause-pipelines:
	fly -t cloudmason unpause-pipeline \
		--pipeline awx
	fly -t cloudmason unpause-pipeline \
		--pipeline octodns

fly-trigger-deploy:
	fly -t cloudmason trigger-job -j awx/deploy

fly-destroy-pipelines:
	fly -t cloudmason destroy-pipeline -p awx
