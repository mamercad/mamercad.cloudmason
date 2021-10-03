.PHONY: shipit

shipit:
	ansible-playbook -i inventory/cloudmason.yml playbooks/site.yml --verbose --ask-vault-password
