## Makefile for deploying s3 static websites
# because we can't remember cli commands

DESCRIPTION="Targets for deploying or updating static s3 web sites"
REGION=us-east-2
AWS_PAGER=

.EXPORT_ALL_VARIABLES:

# Install dependencies
install:
	pnpm install

# Run development server
dev:
	pnpm dev

# Build for production
build:
	pnpm build

# DO NOT copy and paste without changing stack-name and RootDomainName
update-dadpass:
    # Deploy or update s3 static website dadpass.com
	aws cloudformation deploy \
	--template static_web_cdn_dad_pass_template.yml \
	--stack-name dad-pass-static-web-$(REGION) \
	--parameter-overrides RootDomainName=dadpass.com CertificateArn=arn:aws:acm:us-east-1:778590694111:certificate/56181d39-41a9-43fa-b007-3c5a432427f0 \
	--tags \
	Repo=https://github.com/anuvi720/infra/tree/main/s3_web

# Build and deploy to S3
publish: build
	# Sync dist/ contents to S3 bucket
	aws s3 sync dist/ s3://dadpass.com/ --delete


