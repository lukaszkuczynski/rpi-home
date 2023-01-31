workspace := $(shell terraform workspace show)

apply: 
	terraform apply -auto-approve -var-file="${workspace}.tfvars"