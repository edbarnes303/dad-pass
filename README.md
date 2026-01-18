# DadPass 🔑

DadPass is a simple cheap (almost free) to run service I built because my kids kept asking me to send them the Netflix password (and other passwords) in plain text. It is intended for tech dads and tech moms to copy and deploy on their own AWS account, however everyone is welcome to use my deployment at https://dadpass.com so long as you're willing to trust me. I'm also working on a containerized version for tech dads and tech moms who don't roll with serverless.

## What It Does

DadPass allows you to share sensitive information (like passwords) securely by:

-   Creating a temporary, one-time-use link to share a message
-   Auto-destroying the message after it's been retrieved once

Perfect for those "Dad, what's the WiFi password?" moments without sending credentials in plain text over messaging apps.

<img src="dadpassss.png" alt="DadPass Screenshot" width="50%" />

## Architecture

This is a serverless application built on AWS using:

-   **AWS Lambda** (Python 3.12) - Backend logic
-   **API Gateway** (HTTP API) - REST endpoints
-   **DynamoDB** - Persistent message storage with TTL-based expiration
-   **AWS SAM** (Serverless Application Model) - Infrastructure as Code
-   **AWS Lambda Powertools** - Logging and event handling
-   **CloudFront + S3** - Static frontend hosting
-   **React + TypeScript** - Modern frontend with Vite build tooling

### Current Status

✅ **Completed:**

-   Backend API with persistent DynamoDB storage
-   One-time message retrieval with automatic deletion
-   Configurable TTL-based message expiration (15 minutes, 1 hour, 1 day, 5 days)
-   **Server-side encryption at rest** using Fernet symmetric encryption
-   Encryption keys stored securely in AWS SSM Parameter Store
-   React/TypeScript frontend with Vite
-   Message creation and retrieval UI with copy-to-clipboard
-   Character limit (256 characters) with visual feedback
-   Toast notifications and loading states
-   Responsive design with modern CSS

## API Endpoints

### POST `/dad-pass`

Creates a new temporary message and returns a unique key.

**Request Body:**

```json
{
    "message": "The Netflix password is hunter2",
    "ttlOption": "1day"
}
```

Optional `ttlOption` values:

-   `15min` - Message expires in 15 minutes
-   `1hour` - Message expires in 1 hour
-   `1day` - Message expires in 1 day (default)
-   `5days` - Message expires in 5 days

**Note:** Messages are limited to 256 characters.

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
-   Python 3.14
-   An S3 bucket for deployment artifacts

## Setup & Deployment

### 1. Set Environment Variables

```bash
export STAGE=dev  # or prod, staging, local
```

### 2. Create S3 Bucket for Artifacts

The deployment expects an S3 bucket named:

```
<your-service-name>-{STAGE}-lambda-artifacts-us-east-2
```

Create it if it doesn't exist:

```bash
aws s3 mb s3://<your-service-name>-dev-lambda-artifacts-us-east-2 --region us-east-2
```

### 3. Build and Deploy

#### Backend Deployment

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

#### Frontend Deployment

```bash
cd frontend
pnpm install     # Install dependencies
pnpm build       # Build the React app
pnpm deploy      # Deploy to S3 and CloudFront
pnpm update-stack # Update CloudFormation stack (if needed)
```

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

### Backend Local Testing

Run the Lambda code locally:

```bash
cd backend
python run_local.py
```

### View Logs

```bash
cd backend
make tail
```

### Frontend Local Development

Run the frontend dev server:

```bash
cd frontend
pnpm install  # Install dependencies
pnpm dev      # Start dev server at http://localhost:5173
```

## Configuration

Key configuration in [template.yaml](backend/template.yaml):

-   **Runtime**: Python 3.14
-   **Timeout**: 35 seconds
-   **Memory**: 128 MB
-   **Encryption**: Fernet symmetric encryption with master key stored in SSM Parameter Store

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
└── frontend/
    ├── src/
    │   ├── App.tsx             # Main React component
    │   ├── main.tsx            # React entry point
    │   ├── api/
    │   │   └── dadpass.ts      # API client
    │   ├── components/         # Reusable components
    │   │   ├── CopyButton/
    │   │   ├── Spinner/
    │   │   └── Toast/
    │   ├── pages/
    │   │   ├── CreateMessage/  # Message creation page
    │   │   └── ViewMessage/    # Message retrieval page
    │   └── styles/             # Global styles
    ├── static_web_cdn_dad_pass_template.yml  # CloudFront/S3 template
    ├── vite.config.ts          # Vite configuration
    ├── package.json            # Frontend dependencies
    └── Makefile                # Frontend deployment commands
```

## Security Considerations

-   **Messages are encrypted at rest** using Fernet symmetric encryption (cryptography library)
-   Encryption keys stored securely in AWS Systems Manager Parameter Store (encrypted SecureString)
-   TTL-based automatic expiration for all messages (configurable: 15min, 1hour, 1day, 5days)
-   API Gateway uses IAM permissions for Lambda invocation
-   CloudWatch logging enabled for audit trails
-   One-time message retrieval prevents replay attacks
-   256 character limit on messages

## Future Enhancements

-   [ ] Containerized version (Docker/ECS)

## Cost Estimate

Running on AWS Free Tier should keep this nearly free:

-   **Lambda**: First 1M requests/month free
-   **API Gateway**: First 1M requests/month free
-   **DynamoDB**: 25GB storage free, 25 read/write capacity units free
-   **CloudWatch Logs**: 5GB ingestion free
-   **S3**: 5GB storage free, 20,000 GET requests free
-   **CloudFront**: 1TB data transfer out free (for first 12 months)

DadPass scales to zero so if it's not used it doesn't cost anything to run. Even if it's used hundreds of times a month it will be free or almost free to run.

## License

Feel free to use, modify, and deploy for your own family's use.

## Contributing

This is primarily a personal project, but suggestions and improvements are welcome! Open an issue or submit a pull request.

## Questions?

Built with ❤️ by a dad tired telling his kids to call him if they need a password. There are better reasons to call, and better ways to send a password.
