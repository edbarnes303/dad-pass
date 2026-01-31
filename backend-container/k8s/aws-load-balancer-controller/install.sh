#!/bin/bash
# Install AWS Load Balancer Controller using kubectl
# This script downloads the official manifests and applies them

set -e

# Configuration
CONTROLLER_VERSION="${CONTROLLER_VERSION:-v2.7.1}"
CLUSTER_NAME="${CLUSTER_NAME:-dad-pass-cluster-dev}"
AWS_REGION="${AWS_REGION:-us-east-2}"
ALB_ROLE_ARN="${ALB_ROLE_ARN:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing AWS Load Balancer Controller ${CONTROLLER_VERSION}"
echo "Cluster: ${CLUSTER_NAME}"
echo "Region: ${AWS_REGION}"

# Check required variables
if [ -z "$ALB_ROLE_ARN" ]; then
    echo "ERROR: ALB_ROLE_ARN is required"
    exit 1
fi

# Create temp directory for downloaded manifests
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Download the controller manifest
echo "Downloading controller manifest..."
MANIFEST_URL="https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/${CONTROLLER_VERSION}/v2_7_1_full.yaml"
curl -sL "$MANIFEST_URL" -o "$TEMP_DIR/controller.yaml"

# Apply the service account with IRSA annotation
echo "Applying service account..."
sed "s|REPLACE_WITH_ALB_CONTROLLER_ROLE_ARN|${ALB_ROLE_ARN}|g" \
    "$SCRIPT_DIR/service-account.yaml" | kubectl apply -f -

# Modify the downloaded manifest:
# 1. Remove the ServiceAccount (we create our own with IRSA)
# 2. Update cluster-name in the Deployment args
echo "Preparing controller manifest..."
cat "$TEMP_DIR/controller.yaml" | \
    sed '/^apiVersion: v1$/,/^---$/{ /^kind: ServiceAccount$/,/^---$/d; }' | \
    sed "s/--cluster-name=.*$/--cluster-name=${CLUSTER_NAME}/" | \
    sed "s/your-cluster-name/${CLUSTER_NAME}/g" > "$TEMP_DIR/controller-modified.yaml"

# Apply CRDs first (IngressClassParams and TargetGroupBindings)
echo "Applying CRDs..."
CRDS_URL="https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/${CONTROLLER_VERSION}/v2_7_1_crd.yaml"
curl -sL "$CRDS_URL" | kubectl apply -f -

# Apply the controller
echo "Applying controller..."
kubectl apply -f "$TEMP_DIR/controller-modified.yaml"

# Wait for the controller to be ready
echo "Waiting for controller to be ready..."
kubectl wait --for=condition=available --timeout=120s \
    deployment/aws-load-balancer-controller -n kube-system

echo "AWS Load Balancer Controller installed successfully!"
kubectl get deployment aws-load-balancer-controller -n kube-system
