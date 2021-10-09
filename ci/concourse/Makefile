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
		--pipeline hello --config pipelines/hello.yml \
		--var github-access-token="$(shell lpass show Homelab\Concourse/Github --password)" \
		--var slack-webhook="$(shell lpass show Homelab\Concourse/Slack --password)" \
		--non-interactive

fly-unpause-pipelines:
	fly -t cloudmason unpause-pipeline \
		--pipeline hello
