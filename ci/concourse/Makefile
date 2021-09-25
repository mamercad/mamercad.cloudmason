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

fly-test-pipelines:
	fly -t cloudmason validate-pipeline -c pipelines/hello.yml

fly-set-pipelines:
	fly -t cloudmason set-pipeline \
		--pipeline hello --config pipelines/pr.yml \
		--var github-access-token="$(shell cat ~/.github-concourse-access-token)" \
		--non-interactive

fly-unpause-pipelines:
	fly -t cloudmason unpause-pipeline \
		--pipeline hello
