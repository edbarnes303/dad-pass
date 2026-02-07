# Makefile for dad-pass container backend
# Commands for development, testing, and deployment

# Default values (can be overridden via environment variables)
CONTAINER_SERVICE_URL ?= http://localhost:5001
PORT ?= 5001
PYTHONPATH := $(shell pwd)/src:$(PYTHONPATH)

# AWS Configuration
AWS_REGION ?= us-east-2
STAGE ?= dev

# Shared EKS Cluster Configuration
CLUSTER_NAME ?= shared-eks
EKS_STACK_NAME ?= $(CLUSTER_NAME)-$(STAGE)

# App-specific Configuration
ECR_STACK_NAME ?= dad-pass-ecr-$(STAGE)
FARGATE_STACK_NAME ?= dad-pass-fargate-$(STAGE)
IAM_STACK_NAME ?= dad-pass-iam-$(STAGE)

# Docker/ECR Configuration
AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
ECR_REGISTRY := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPO_NAME := dad-pass-$(STAGE)
IMAGE_TAG ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")
IMAGE_URI := $(ECR_REGISTRY)/$(ECR_REPO_NAME):$(IMAGE_TAG)

.EXPORT_ALL_VARIABLES:

.PHONY: help install test test-unit test-integration run clean \
        deploy-ecr deploy-fargate deploy-iam deploy-app-infra \
        ecr-login docker-build docker-push docker-deploy \
        k8s-configure k8s-deploy k8s-rollout k8s-status k8s-logs \
        get-alb-url full-deploy

help:
	@echo "Dad-Pass Container Backend"
	@echo ""
	@echo "Configuration:"
	@echo "  CLUSTER_NAME=$(CLUSTER_NAME)"
	@echo "  STAGE=$(STAGE)"
	@echo "  AWS_REGION=$(AWS_REGION)"
	@echo ""
	@echo "Development:"
	@echo "  make install              - Install dependencies"
	@echo "  make test                 - Run all tests"
	@echo "  make test-unit            - Run unit tests only"
	@echo "  make test-integration     - Run integration tests only"
	@echo "  make run                  - Run the Flask development server"
	@echo "  make clean                - Clean up cache files"
	@echo ""
	@echo "App Infrastructure (CloudFormation):"
	@echo "  make deploy-ecr           - Deploy ECR repository"
	@echo "  make deploy-fargate       - Deploy Fargate profile"
	@echo "  make deploy-iam           - Deploy app IAM role (IRSA)"
	@echo "  make deploy-app-infra     - Deploy all app infrastructure"
	@echo ""
	@echo "Docker/ECR:"
	@echo "  make ecr-login            - Authenticate Docker to ECR"
	@echo "  make docker-build         - Build Docker image"
	@echo "  make docker-push          - Push image to ECR"
	@echo "  make docker-deploy        - Build and push image"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-configure        - Configure kubectl for EKS cluster"
	@echo "  make k8s-deploy           - Deploy application to Kubernetes"
	@echo "  make k8s-rollout          - Trigger rolling restart of deployment"
	@echo "  make k8s-status           - Show deployment status"
	@echo "  make k8s-logs             - Show application logs"
	@echo "  make get-alb-url          - Get the ALB URL"
	@echo ""
	@echo "Full Deployment:"
	@echo "  make full-deploy          - Complete app deployment"
	@echo ""
	@echo "Note: EKS cluster must be deployed first using ../infra/Makefile"

#############################################
# Development
#############################################

install:
	pip install -r app/requirements.txt
	pip install -r tests/requirements.txt

test: test-unit

test-unit:
	PYTHONPATH=$(PYTHONPATH) pytest tests/unit/ -v

test-integration:
	CONTAINER_SERVICE_URL=$(CONTAINER_SERVICE_URL) pytest tests/integration/ -v

run:
	cd app && python app.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true


#############################################
# Docker/ECR Commands
#############################################

ecr-login:
	@echo "Logging into ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | \
		docker login --username AWS --password-stdin $(ECR_REGISTRY)

docker-build:
	@echo "Building Docker image: $(IMAGE_URI)"
	docker build --platform linux/amd64 -t $(ECR_REPO_NAME):$(IMAGE_TAG) -t $(ECR_REPO_NAME):latest ./app
	docker tag $(ECR_REPO_NAME):$(IMAGE_TAG) $(IMAGE_URI)
	docker tag $(ECR_REPO_NAME):latest $(ECR_REGISTRY)/$(ECR_REPO_NAME):latest

docker-push: ecr-login
	@echo "Pushing image to ECR: $(IMAGE_URI)"
	docker push $(IMAGE_URI)
	docker push $(ECR_REGISTRY)/$(ECR_REPO_NAME):latest

docker-deploy: docker-build docker-push
	@echo "Docker image built and pushed: $(IMAGE_URI)"


#############################################
# App Infrastructure Deployment
#############################################

deploy-ecr:
	@echo "Deploying ECR repository for dad-pass..."
	aws cloudformation deploy \
		--template-file infra/ecr.yml \
		--stack-name $(ECR_STACK_NAME) \
		--parameter-overrides \
			StageName=$(STAGE) \
		--capabilities CAPABILITY_NAMED_IAM \
		--region $(AWS_REGION)
	@echo "ECR Repository URI:"
	@aws cloudformation describe-stacks \
		--stack-name $(ECR_STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue' \
		--output text \
		--region $(AWS_REGION)

deploy-fargate:
	@echo "Deploying Fargate profile for dad-pass..."
	aws cloudformation deploy \
		--template-file infra/fargate-profile.yml \
		--stack-name $(FARGATE_STACK_NAME) \
		--parameter-overrides \
			StageName=$(STAGE) \
			EKSStackName=$(EKS_STACK_NAME) \
		--capabilities CAPABILITY_NAMED_IAM \
		--region $(AWS_REGION)
	@echo "Fargate profile deployed."

deploy-iam:
	@echo "Deploying IAM role for dad-pass pods..."
	aws cloudformation deploy \
		--template-file infra/app-iam.yml \
		--stack-name $(IAM_STACK_NAME) \
		--parameter-overrides \
			StageName=$(STAGE) \
			EKSStackName=$(EKS_STACK_NAME) \
		--capabilities CAPABILITY_NAMED_IAM \
		--region $(AWS_REGION)
	@echo "IAM Role ARN:"
	@aws cloudformation describe-stacks \
		--stack-name $(IAM_STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`AppPodRoleArn`].OutputValue' \
		--output text \
		--region $(AWS_REGION)

deploy-app-infra: deploy-ecr deploy-fargate deploy-iam
	@echo "All app infrastructure deployed successfully!"


#############################################
# Kubernetes Commands
#############################################

k8s-configure:
	@echo "Configuring kubectl for EKS cluster: $(CLUSTER_NAME)-$(STAGE)"
	aws eks update-kubeconfig \
		--name $(CLUSTER_NAME)-$(STAGE) \
		--region $(AWS_REGION)
	kubectl config current-context

k8s-deploy:
	@echo "Deploying application to Kubernetes..."
	@# Get values from CloudFormation
	$(eval ECR_URI := $(shell aws cloudformation describe-stacks \
		--stack-name $(ECR_STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue' \
		--output text \
		--region $(AWS_REGION)))
	$(eval APP_ROLE_ARN := $(shell aws cloudformation describe-stacks \
		--stack-name $(IAM_STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`AppPodRoleArn`].OutputValue' \
		--output text \
		--region $(AWS_REGION)))
	@echo "ECR URI: $(ECR_URI)"
	@echo "App Role ARN: $(APP_ROLE_ARN)"
	@# Apply namespace first
	kubectl apply -f k8s/namespace.yaml
	@# Apply service account with role ARN substitution
	cat k8s/service-account.yaml | \
		sed 's|REPLACE_WITH_APP_POD_ROLE_ARN|$(APP_ROLE_ARN)|g' | \
		kubectl apply -f -
	@# Apply deployment with substitutions
	cat k8s/deployment.yaml | \
		sed 's|REPLACE_WITH_ECR_URI|$(ECR_URI)|g' | \
		sed 's|REPLACE_WITH_IMAGE_TAG|$(IMAGE_TAG)|g' | \
		sed 's|REPLACE_WITH_TABLE_NAME|dad-pass-service-messages-prod|g' | \
		sed 's|REPLACE_WITH_AWS_REGION|$(AWS_REGION)|g' | \
		sed 's|REPLACE_WITH_STAGE|$(STAGE)|g' | \
		kubectl apply -f -
	@# Apply service and ingress
	kubectl apply -f k8s/service.yaml
	cat k8s/ingress.yaml | \
		sed 's|Environment=dev|Environment=$(STAGE)|g' | \
		kubectl apply -f -
	@echo "Application deployed. Waiting for pods to be ready..."
	kubectl wait --for=condition=ready pod -l app=dad-pass -n dad-pass --timeout=120s || true
	@echo "Run 'make get-alb-url' to get the ALB URL (may take a few minutes to provision)"

k8s-rollout:
	@echo "Triggering rolling restart..."
	kubectl rollout restart deployment/dad-pass -n dad-pass
	kubectl rollout status deployment/dad-pass -n dad-pass

k8s-status:
	@echo "=== Deployment Status ==="
	kubectl get deployment -n dad-pass
	@echo ""
	@echo "=== Pod Status ==="
	kubectl get pods -n dad-pass
	@echo ""
	@echo "=== Service Status ==="
	kubectl get svc -n dad-pass
	@echo ""
	@echo "=== Ingress Status ==="
	kubectl get ingress -n dad-pass

k8s-logs:
	kubectl logs -l app=dad-pass -n dad-pass --tail=100 -f

get-alb-url:
	@echo "ALB URL:"
	@ALB_HOST=$$(kubectl get ingress dad-pass -n dad-pass -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null) && \
		if [ -n "$$ALB_HOST" ]; then \
			echo "http://$$ALB_HOST/dad-pass"; \
		else \
			echo "ALB not yet provisioned. Wait a few minutes and try again."; \
		fi
	@echo ""

#############################################
# Deployment
#############################################

full-deploy: deploy-app-infra k8s-configure docker-deploy k8s-deploy
	@echo ""
	@echo "========================================="
	@echo "Dad-pass deployment complete!"
	@echo "========================================="
	@echo ""
	@make get-alb-url


# Deploy updated app (build/push image and update k8s deployment)
deploy-app: docker-deploy k8s-deploy
	@echo ""
	@echo "========================================="
	@echo "App update complete!"
	@echo "========================================="
	@echo ""

