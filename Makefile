build:
	poetry run stacker build --region us-east-1 ./stacker.yaml
	poetry run stacker info --region us-east-1 ./stacker.yaml
