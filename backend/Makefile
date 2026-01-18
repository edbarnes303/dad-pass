# Makefile for dad-pass api.
# because we can't remember cli commands

# Must set STAGE in your shell first ex: export STAGE=prod


# Pulls environment variables from ../evn/dev.env if present before running any rule
# (https://lithic.tech/blog/2020-05/makefile-dot-env/)
ifdef STAGE
	ifneq (,$(wildcard ../env/$(STAGE).env))
		include ../env/$(STAGE).env
		export
	endif
endif

# IMPORTANT!!! - If you copied this DO NOT deploy before changing the value of SERVICE_PATH to ensure you don't stomp
# on an existing deployed stack
SERVICE_PATH=dad-pass
FUNCTION=$(SERVICE_PATH)-service
MESSAGES_TABLE_NAME=$(FUNCTION)-messages-$(STAGE)
DESCRIPTION="Service for $(SERVICE_PATH) data"
REGION=us-east-2
AWS_PAGER=
S3_BUCKET="dad-pass-$(STAGE)-lambda-artifacts-$(REGION)"
STACK_NAME="$(FUNCTION)-$(REGION)-$(STAGE)"
PYTHONPATH=$(shell pwd)/src:$(shell pwd)/../shared/src

.EXPORT_ALL_VARIABLES:

print-stage:
	@echo
	@echo '***** STAGE=$(STAGE) *****'
	@echo

clean:
	@echo 'Removing crap'
	rm -rf dist
	rm -rf .aws-sam
	rm -rf package.*
	find . -name .pytest_cache | xargs rm -rf
	find . -name __pycache__ | xargs rm -rf

build: clean
	sam build

package: build
	@if test -z "$(STAGE)"; then echo "****** STAGE not set. Set STAGE with: export STAGE=env ******"; exit 1; fi
	sam package \
	--s3-bucket $(S3_BUCKET) \
	--output-template-file "package.$(STAGE).yaml"

deploy: print-stage package
	sam deploy \
	--no-fail-on-empty-changeset \
	--template-file "package.$(STAGE).yaml" \
	--stack-name $(STACK_NAME) \
	--capabilities CAPABILITY_IAM \
	--region $(REGION) \
	--parameter-overrides StageName=$(STAGE) ServiceName=$(FUNCTION) ServicePath=$(SERVICE_PATH)

deploy-ci: test-unit deploy-no-tests
	$(MAKE) test-integration

invoke:
	aws lambda invoke --invocation-type RequestResponse --function-name $(FUNCTION)-$(STAGE) --payload '{"route": "set_message", "args": {"message": "Hello, World!"}}' --cli-binary-format raw-in-base64-out /dev/stdout

# Run a custom event locally and see it's entire output. Good for iterating fast on your local machine.
# Use this as a refernce for how to run and debug the lambda code locally in your IDE.
run-local:
	python run_local.py CREATE_MESSAGE

test-unit:
	pytest -v tests/unit

test-integration:
	pytest -v tests/integration


tail:
	aws logs tail --follow --format short /aws/lambda/$(FUNCTION)-$(STAGE)


delete-stack:
	aws cloudformation delete-stack --stack-name $(STACK_NAME)


.PHONY : package