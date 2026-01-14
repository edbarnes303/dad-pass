# DadPass 🔑

DadPass is a simple cheap (almost free) to run service I built because my kids kept asking me to send them the Netflix password (and other passwords) in plain text. It is intended for tech dads and tech moms to copy and deploy on their own AWS account, however everyone is welcome to use my deployment so long as you're willing to trust me. I'm also working on a containerized version for tech dads and tech moms who don't roll with serverless.

## What It Does

DadPass allows you to share sensitive information (like passwords) securely by:

-   Creating a temporary, one-time-use link to share a message
-   Auto-destroying the message after it's been retrieved once
-   Using a simple REST API that can be accessed from anywhere

Perfect for those "Dad, what's the WiFi password?" moments without sending credentials in plain text over messaging apps.

## Architecture

This is a serverless application built on AWS using:

-   **AWS Lambda** (Python 3.12) - Backend logic
-   **API Gateway** (HTTP API) - REST endpoints
-   **AWS SAM** (Serverless Application Model) - Infrastructure as Code
-   **AWS Lambda Powertools** - Logging and event handling

### Current Limitations

⚠️ **Note**: The current implementation stores messages in-memory within the Lambda function. This means:

-   Messages are lost when the Lambda function cold-starts
-   Not suitable for production use without persistence (DynamoDB recommended)
-   Fine for demo/testing purposes
-   Fontend is not yet available, comming soon.

## API Endpoints

### POST `/dad-pass`

Creates a new temporary message and returns a unique key.

**Request Body:**

```json
{
    "message": "The Netflix password is hunter2"
}
```

**Response:**

```json
{
    "messageKey": "aB3d5"
}
```

### GET `/dad-pass/{messageKey}`

Retrieves and deletes a message by its key.

**Response:**

```json
{
    "message": "The Netflix password is hunter2"
}
```

After retrieval, the message is permanently deleted.

## Prerequisites

-   AWS Account with appropriate permissions
-   AWS CLI configured with credentials
-   AWS SAM CLI installed
-   Python 3.12
-   An S3 bucket for deployment artifacts

## Setup & Deployment

### 1. Set Environment Variables

```bash
export STAGE=dev  # or prod, staging, local
```

### 2. Create S3 Bucket for Artifacts

The deployment expects an S3 bucket named:

```
dad-pass-{STAGE}-lambda-artifacts-us-east-2
```

Create it if it doesn't exist:

```bash
aws s3 mb s3://dad-pass-dev-lambda-artifacts-us-east-2 --region us-east-2
```

### 3. Build and Deploy

Using the Makefile:

```bash
cd backend
make deploy
```

This will:

-   Clean previous builds
-   Build the Lambda function
-   Package it to S3
-   Deploy via CloudFormation

### Manual Deployment

If you prefer not to use Make:

```bash
cd backend

# Build
sam build

# Package
sam package \
  --s3-bucket dad-pass-dev-lambda-artifacts-us-east-2 \
  --output-template-file package.dev.yaml

# Deploy
sam deploy \
  --template-file package.dev.yaml \
  --stack-name dad-pass-service-us-east-2-dev \
  --capabilities CAPABILITY_IAM \
  --region us-east-2 \
  --parameter-overrides StageName=dev ServiceName=dad-pass-service ServicePath=dad-pass
```

## Development

### Local Testing

Run the Lambda locally:

```bash
cd backend
python run_local.py
```

### Integration Tests

```bash
cd backend
make test-integration
```

### View Logs

```bash
cd backend
make tail
```

## Configuration

Key configuration in [template.yaml](backend/template.yaml):

-   **Runtime**: Python 3.12
-   **Timeout**: 35 seconds
-   **Memory**: 128 MB
-   **VPC**: Configured to use existing security groups and subnets (via SSM parameters)

Environment-specific settings:

-   **dev**: DEBUG logging
-   **prod**: INFO logging

## Project Structure

```
dad-pass/
├── backend/
│   ├── src/
│   │   ├── lambda_function.py  # Main Lambda handler
│   │   ├── utils.py            # Utility functions
│   │   └── requirements.txt    # Python dependencies
│   ├── tests/
│   │   └── integration/        # Integration tests
│   ├── template.yaml           # SAM template
│   ├── Makefile                # Build/deploy commands
│   └── run_local.py            # Local testing script
└── frontend/                   # (Coming soon)
```

## Security Considerations

-   Messages are currently stored in-memory (ephemeral)
-   VPC configuration restricts Lambda network access
-   API Gateway uses IAM permissions for Lambda invocation
-   CloudWatch logging enabled for audit trails
-   One-time message retrieval prevents replay attacks

## Future Enhancements

-   [ ] DynamoDB persistence for messages
-   [ ] TTL-based message expiration
-   [ ] Message encryption at rest
-   [ ] Frontend UI for easy message creation/retrieval
-   [ ] Containerized version (Docker/ECS)

## Cost Estimate

Running on AWS Free Tier should keep this nearly free:

-   **Lambda**: First 1M requests/month free
-   **API Gateway**: First 1M requests/month free
-   **CloudWatch Logs**: 5GB ingestion free

For typical family use (dozens of password shares per month), expect costs under $1/month.

## License

Feel free to use, modify, and deploy for your own family's use.

## Contributing

This is primarily a personal project, but suggestions and improvements are welcome! Open an issue or submit a pull request.

## Questions?

Built with ❤️ by a dad tired of sending passwords over text.
