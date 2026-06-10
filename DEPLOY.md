# AutoResearch — Multi-Server Deployment with SQS

## Architecture

```
                          ┌──────────────┐
User ──→ ALB ──→ API (FastAPI) ──→ SQS Queue ──→ EC2 Worker 1
                          │                    ├→ EC2 Worker 2
                          │                    ├→ EC2 Worker N
                          │                    └→ (auto-scale group)
                          │
                          └──→ RDS (PostgreSQL)
```

## Step 1: Create Shared Resources

### 1a. RDS PostgreSQL (replace SQLite)

```bash
aws rds create-db-instance \
  --db-instance-identifier autoresearch-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username autoresearch \
  --master-user-password <your-password> \
  --allocated-storage 20 \
  --publicly-accessible
```

Get the endpoint and set:
```bash
export DATABASE_URL="postgresql://autoresearch:<password>@<rds-endpoint>:5432/autoresearch"
```

### 1b. SQS Queue

```bash
# Standard queue (not FIFO)
aws sqs create-queue --queue-name autoresearch-jobs

# Get the queue URL
aws sqs get-queue-url --queue-name autoresearch-jobs

# Set a DLQ for failed messages (optional but recommended)
aws sqs create-queue --queue-name autoresearch-jobs-dlq
DLQ_ARN=$(aws sqs get-queue-attributes --queue-url <dlq-url> --attribute-names QueueArn | jq -r .Attributes.QueueArn)

aws sqs set-queue-attributes \
  --queue-url <queue-url> \
  --attributes '{"RedrivePolicy": "{\"deadLetterTargetArn\": \"'$DLQ_ARN'\", \"maxReceiveCount\": \"3\"}"}'
```

### 1c. IAM Role for EC2 instances

Create an IAM role `autoresearch-worker` with this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "<sqs-queue-arn>"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage"
      ],
      "Resource": "<sqs-queue-arn>"
    }
  ]
}
```

Attach to EC2 instances at launch.

## Step 2: Launch EC2 Instances

### API Server (frontend + API endpoint)

```bash
# On each API EC2 instance
export SQS_QUEUE_URL="<your-queue-url>"
export DATABASE_URL="postgresql://autoresearch:<password>@<rds-endpoint>:5432/autoresearch"
export AWS_REGION="us-east-1"

cd ~/autoresearch/backend
pip install -r requirements.txt
python main.py
```

### Worker Instances (auto-scaled)

Create an AMI or use user-data to run the worker on boot:

```bash
# On each worker EC2 instance (user-data script)
#!/bin/bash
export SQS_QUEUE_URL="<your-queue-url>"
export DATABASE_URL="postgresql://autoresearch:<password>@<rds-endpoint>:5432/autoresearch"
export AWS_REGION="us-east-1"

cd /home/ubuntu/autoresearch/backend
source venv_backup/bin/activate
pip install -r requirements.txt

nohup python worker.py > /var/log/autoresearch-worker.log 2>&1 &
```

Create an Auto Scaling Group for workers based on SQS queue depth
(`ApproximateNumberOfMessagesVisible` metric).

### Frontend (Next.js)

No changes needed — it's stateless and just calls the API.

```bash
cd ~/autoresearch/frontend
npm run build
npx next start -p 3000
```

## Step 3: Local Development

For local testing without AWS, everything still works with SQLite and no SQS:

```bash
cd ~/autoresearch/backend
source venv_backup/bin/activate
python main.py
```

Jobs will be created with status `no_worker` — run the worker locally:

```bash
# Terminal 1: API
cd ~/autoresearch/backend && source venv_backup/bin/activate && python main.py

# Terminal 2: worker (uses the same SQLite DB)
cd ~/autoresearch/backend && source venv_backup/bin/activate && \
  SQS_QUEUE_URL="<your-queue-url>" python worker.py
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | No | `sqlite:///data/autoresearch.db` | PostgreSQL URL for production |
| `SQS_QUEUE_URL` | No | `""` | SQS queue URL (empty = no worker mode) |
| `AWS_REGION` | No | `us-east-1` | AWS region |
| `WORKER_POLL_INTERVAL` | No | `5` | SQS long-poll wait time (seconds) |
| `WORKER_MAX_MESSAGES` | No | `3` | Max messages per poll |
| `WORKER_VISIBILITY_TIMEOUT` | No | `600` | Job processing timeout (seconds) |
