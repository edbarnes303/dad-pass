# Makefile for dad-pass container backend
# Commands for development, testing, and deployment

# Default values (can be overridden via environment variables)
CONTAINER_SERVICE_URL ?= http://localhost:5001
PORT ?= 5001
PYTHONPATH := $(shell pwd)/src:$(PYTHONPATH)

# AWS/EKS Configuration
AWS_REGION ?= us-east-2
STAGE ?= dev
CLUSTER_NAME ?= dad-pass-cluster-$(STAGE)
ECR_STACK_NAME ?= dad-pass-ecr-$(STAGE)
EKS_STACK_NAME ?= dad-pass-eks-$(STAGE)

# Docker/ECR Configuration
AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
ECR_REGISTRY := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPO_NAME := dad-pass-backend-$(STAGE)
IMAGE_TAG ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")
IMAGE_URI := $(ECR_REGISTRY)/$(ECR_REPO_NAME):$(IMAGE_TAG)

.EXPORT_ALL_VARIABLES:

.PHONY: help install test test-unit test-integration run clean \
        deploy-ecr deploy-eks deploy-infra \
        ecr-login docker-build docker-push docker-deploy \
        k8s-configure k8s-deploy k8s-rollout k8s-status k8s-logs \
        install-alb-controller get-alb-url

help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install              - Install dependencies"
	@echo "  make test                 - Run all tests"
	@echo "  make test-unit            - Run unit tests only"
	@echo "  make test-integration     - Run integration tests only"
	@echo "  make run                  - Run the Flask development server"
	@echo "  make clean                - Clean up cache files"
	@echo ""
	@echo "Infrastructure (CloudFormation):"
	@echo "  make deploy-ecr           - Deploy ECR repository stack"
	@echo "  make deploy-eks           - Deploy EKS cluster stack"
	@echo "  make deploy-infra         - Deploy all infrastructure (ECR + EKS)"
	@echo ""
	@echo "Docker/ECR:"
	@echo "  make ecr-login            - Authenticate Docker to ECR"
	@echo "  make docker-build         - Build Docker image"
	@echo "  make docker-push          - Push image to ECR"
	@echo "  make docker-deploy        - Build and push image"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-configure        - Configure kubectl for EKS cluster"
	@echo "  make install-alb-controller - Install AWS Load Balancer Controller"
	@echo "  make k8s-deploy           - Deploy application to Kubernetes"
	@echo "  make k8s-rollout          - Trigger rolling restart of deployment"
	@echo "  make k8s-status           - Show deployment status"
	@echo "  make k8s-logs             - Show application logs"
	@echo "  make get-alb-url          - Get the ALB URL"
	@echo ""
	@echo "Full Deployment:"
	@echo "  make full-deploy          - Complete deployment (infra + app)"

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
# Infrastructure Deployment
#############################################

deploy-ecr:
	@echo "Deploying ECR repository..."
	aws cloudformation deploy \
		--template-file infra/ecr.yml \
		--stack-name $(ECR_STACK_NAME) \
		--parameter-overrides StageName=$(STAGE) \
		--capabilities CAPABILITY_NAMED_IAM \
		--region $(AWS_REGION)
	@echo "ECR Repository URI:"
	@aws cloudformation describe-stacks \
		--stack-name $(ECR_STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue' \
		--output text \
		--region $(AWS_REGION)

deploy-eks:
	@echo "Deploying EKS cluster (this may take 15-20 minutes)..."
	aws cloudformation deploy \
		--template-file infra/eks-cluster.yml \
		--stack-name $(EKS_STACK_NAME) \
		--parameter-overrides StageName=$(STAGE) \
		--capabilities CAPABILITY_NAMED_IAM \
		--region $(AWS_REGION)
	@echo "EKS Cluster deployed. Run 'make k8s-configure' to configure kubectl."

deploy-infra: deploy-ecr deploy-eks
	@echo "All infrastructure deployed successfully!"

#############################################
# Docker/ECR Commands
#############################################

ecr-login:
	@echo "Logging into ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | \
		docker login --username AWS --password-stdin $(ECR_REGISTRY)

docker-build:
	@echo "Building Docker image: $(IMAGE_URI)"
	docker build -t $(ECR_REPO_NAME):$(IMAGE_TAG) -t $(ECR_REPO_NAME):latest ./app
	docker tag $(ECR_REPO_NAME):$(IMAGE_TAG) $(IMAGE_URI)
	docker tag $(ECR_REPO_NAME):latest $(ECR_REGISTRY)/$(ECR_REPO_NAME):latest

docker-push: ecr-login
	@echo "Pushing image to ECR: $(IMAGE_URI)"
	docker push $(IMAGE_URI)
	docker push $(ECR_REGISTRY)/$(ECR_REPO_NAME):latest

docker-deploy: docker-build docker-push
	@echo "Docker image built and pushed: $(IMAGE_URI)"

#############################################
# Kubernetes Commands
#############################################

k8s-configure:
	@echo "Configuring kubectl for EKS cluster: $(CLUSTER_NAME)"
	aws eks update-kubeconfig \
		--name $(CLUSTER_NAME) \
		--region $(AWS_REGION)
	kubectl config current-context

install-alb-controller:
	@echo "Installing AWS Load Balancer Controller..."
	@# Get the ALB Controller Role ARN from CloudFormation
	$(eval ALB_ROLE_ARN := $(shell aws cloudformation describe-stacks \
		--stack-name $(EKS_STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`ALBControllerRoleArn`].OutputValue' \
		--output text \
		--region $(AWS_REGION)))
	@echo "Using ALB Controller Role ARN: $(ALB_ROLE_ARN)"
	@# Run the install script
	CLUSTER_NAME=$(CLUSTER_NAME) \
	AWS_REGION=$(AWS_REGION) \
	ALB_ROLE_ARN=$(ALB_ROLE_ARN) \
	bash k8s/aws-load-balancer-controller/install.sh

k8s-deploy:
	@echo "Deploying application to Kubernetes..."
	@# Get values from CloudFormation
	$(eval ECR_URI := $(shell aws cloudformation describe-stacks \
		--stack-name $(ECR_STACK_NAME) \
		--query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue' \
		--output text \
		--region $(AWS_REGION)))
	$(eval APP_ROLE_ARN := $(shell aws cloudformation describe-stacks \
		--stack-name $(EKS_STACK_NAME) \
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
	@# Apply deployment with ECR URI substitution
	cat k8s/deployment.yaml | \
		sed 's|REPLACE_WITH_ECR_URI|$(ECR_URI)|g' | \
		sed 's|dad-pass-messages-dev|dad-pass-messages-$(STAGE)|g' | \
		sed 's|us-east-2|$(AWS_REGION)|g' | \
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
	@kubectl get ingress dad-pass -n dad-pass -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || \
		echo "ALB not yet provisioned. Wait a few minutes and try again."
	@echo ""

#############################################
# Full Deployment
#############################################

full-deploy: deploy-infra k8s-configure install-alb-controller docker-deploy k8s-deploy
	@echo ""
	@echo "========================================="
	@echo "Full deployment complete!"
	@echo "========================================="
	@echo ""
	@make get-alb-url
