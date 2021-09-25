T := cloudmason
C := https://concourse.cloudmason.org

.PHONY: fly-login fly-sync fly-targets fly-status fly-userinfo fly-pipelines \
        fly-nuke-pipelines fly-test-pipelines fly-set-pipelines \
				fly-pause-pipeline fly-unpause-pipelines

fly-login:
	@fly login -t $(T) -c $(C)

fly-sync:
	fly -t $(T) sync

fly-targets:
	fly targets

fly-status:
	fly -t $(T) status

fly-userinfo:
	fly -t $(T) userinfo

fly-pipelines:
	fly -t $(T) pipelines

fly-nuke-pipelines:
	fly -t $(T) destroy-pipeline -p hello --non-interactive

fly-test-pipelines:
	fly -t $(T) validate-pipeline -c pipelines/cloudmason.yml

fly-set-pipelines:
	fly -t $(T) set-pipeline \
		--pipeline cloudmason --config pipelines/cloudmason.yml \
		--var github-access-token="$(shell cat ~/.concourse-github-access-token)" \
		--var slack-webhook="$(shell cat ~/.concourse-slack-webhook)" \
		--non-interactive

fly-pause-pipelines:
	fly -t $(T) pause-pipeline \
		--pipeline cloudmason

fly-unpause-pipelines:
	fly -t $(T) unpause-pipeline \
		--pipeline cloudmason
