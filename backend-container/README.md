# Dad Pass - Container Backend

A containerized Flask API for securely storing and retrieving one-time encrypted messages.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- AWS credentials configured locally (`~/.aws/credentials`)
- An AWS account with:
    - A DynamoDB table for storing messages
    - An SSM Parameter Store entry at `/dad-pass/encryption-key` containing your Fernet encryption key

## Setup

1. **Copy the environment template:**

    ```bash
    cp .env.example .env
    ```

2. **Edit `.env` with your configuration:**

    ```bash
    AWS_REGION=us-east-2
    AWS_PROFILE=your-aws-profile-name
    MESSAGES_TABLE_NAME=your-dynamodb-table-name
    ```

    - `AWS_REGION`: The AWS region where your DynamoDB table and SSM parameter are located
    - `AWS_PROFILE`: The name of your AWS profile from `~/.aws/credentials`
    - `MESSAGES_TABLE_NAME`: The name of your DynamoDB table

## Running the Container

**Start the application:**

```bash
docker compose up --build
```

**Run in detached mode (background):**

```bash
docker compose up --build -d
```

**Stop the application:**

```bash
docker compose down
```

The API will be available at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint                  | Description                                     |
| ------ | ------------------------- | ----------------------------------------------- |
| GET    | `/`                       | Health check                                    |
| POST   | `/dad-pass`               | Create a new encrypted message                  |
| GET    | `/dad-pass/<message_key>` | Retrieve and delete a message (one-time access) |

### Create a Message

```bash
curl -X POST http://localhost:8000/dad-pass \
  -H "Content-Type: application/json" \
  -d '{"message": "your secret message", "ttlOption": "1hour"}'
```

**TTL Options:** `15min`, `1hour`, `1day`, `5days`

**Response:**

```json
{ "messageKey": "abc123XYZ" }
```

### Retrieve a Message

```bash
curl http://localhost:8000/dad-pass/abc123XYZ
```

**Response:**

```json
{ "message": "your secret message", "ttlOption": "1hour" }
```

> ⚠️ **Note:** Messages are deleted immediately after retrieval (one-time access).

## AWS Resources Required

### DynamoDB Table

Create a table with:

- **Partition key:** `messageKey` (String)
- **TTL attribute:** `ttl`

### SSM Parameter

Create a SecureString parameter at `/dad-pass/encryption-key` containing a valid Fernet key.

**Generate a Fernet key:**

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## Troubleshooting

**"Unable to locate credentials" error:**

- Ensure your AWS credentials are configured in `~/.aws/credentials`
- Verify the `AWS_PROFILE` in your `.env` matches a profile in your credentials file

**"ResourceNotFoundException" error:**

- Check that your DynamoDB table exists in the specified region
- Verify the `MESSAGES_TABLE_NAME` in your `.env` is correct

**Container won't start:**

- Ensure Docker Desktop is running
- Check logs with `docker compose logs`
