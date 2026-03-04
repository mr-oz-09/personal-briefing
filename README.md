# 📧 Personal Briefing

> Your daily AI-powered tech news briefing, delivered straight to your inbox

A serverless AWS application that automatically collects, summarizes, and emails you a daily briefing of tech news across your favorite topics. Powered by **Tavily AI** for web search, **Amazon Bedrock (Claude)** for intelligent summarization, and **Amazon SES** for email delivery.

![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20Bedrock%20%7C%20SES-orange)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![CDK](https://img.shields.io/badge/CDK-TypeScript-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **🤖 AI-Powered** - Claude 3.5 Sonnet generates witty, insightful summaries
- **🔍 Smart Search** - Tavily AI finds relevant, recent articles (last 3 days)
- **📊 Quality Control** - AI validates article relevance before including
- **🎨 Beautiful Emails** - Modern HTML design with gradients and executive summary
- **⚡ Serverless** - Fully managed AWS infrastructure (Lambda + EventBridge)
- **🔐 Secure** - Secrets stored in AWS Systems Manager Parameter Store
- **💰 Low Cost** - ~$5-6/month (Lambda + Bedrock + SES)
- **📅 Daily Delivery** - Automated 6 AM EST briefings

## 📸 What It Looks Like

Your daily briefing includes:
- **Engaging Intro** - Fun, conversational opening (purple gradient box)
- **Executive Summary** - "Here's what matters today" overview (golden box)
- **Topic Sections** - Curated articles with witty AI summaries
- **Clean Layout** - Professional, easy-to-read design

Default Topics:
- 🤖 AI & Machine Learning
- 🔌 API Design
- 🏗️ Infrastructure Architecture
- ☸️ Kubernetes
- 🔄 SDLC (Software Development Lifecycle)
- 🏗️ Infrastructure as Code

## 🚀 Quick Start

### Prerequisites

- **AWS Account** with appropriate permissions
- **Python 3.11+** and Poetry
- **Node.js 20+** for AWS CDK
- **Tavily AI API Key** (free tier: 1,000 searches/month) - [Get one here](https://tavily.com)

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/personal-briefing.git
cd personal-briefing
poetry install
cd cdk && poetry install --with cdk
```

### 2. Configure AWS Secrets

Store your secrets in AWS Systems Manager Parameter Store:

```bash
# Tavily AI API Key
aws ssm put-parameter \
  --name "/personal-briefing/tavily-api-key" \
  --value "your-tavily-api-key-here" \
  --type "SecureString" \
  --region us-east-2

# Your email address (recipient)
aws ssm put-parameter \
  --name "/personal-briefing/recipient-email" \
  --value "your-email@example.com" \
  --type "String" \
  --region us-east-2

# Sender email (must be verified in SES)
aws ssm put-parameter \
  --name "/personal-briefing/sender-email" \
  --value "briefing@example.com" \
  --type "String" \
  --region us-east-2
```

### 3. Verify SES Email

Amazon SES requires email verification:

```bash
aws ses verify-email-identity \
  --email-address your-email@example.com \
  --region us-east-2
```

**Check your inbox** and click the verification link!

### 4. Enable Bedrock Models

Go to AWS Console → Bedrock → Model Access → Enable **Claude 3.5 Sonnet**

Or via CLI:
```bash
aws bedrock list-foundation-models \
  --region us-east-2 \
  --query 'modelSummaries[?contains(modelId, `claude-3-5`)].modelId'
```

### 5. Customize Topics (Optional)

Edit `config/topics.yaml` to add/remove topics or change the schedule.

### 6. Deploy to AWS

```bash
cd cdk
poetry run cdk bootstrap  # First time only
poetry run cdk deploy
```

### 7. Test It!

Trigger a manual run to test:

```bash
aws lambda invoke \
  --function-name personal-briefing \
  --region us-east-2 \
  /tmp/response.json

cat /tmp/response.json
```

Check your email! 📬

## 📖 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  EventBridge (Cron: 6 AM EST Daily)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Lambda Function (Python 3.11)                              │
│                                                              │
│  1. 🔍 Collect Articles                                     │
│     └─ Tavily AI web search (topic-based, last 3 days)     │
│                                                              │
│  2. 🤖 Summarize with AI                                    │
│     ├─ Validate relevance                                   │
│     ├─ Generate summaries (Claude 3.5 Sonnet)              │
│     ├─ Create intro & executive summary                     │
│     └─ Filter low-quality content                           │
│                                                              │
│  3. 📧 Send Email                                           │
│     └─ Amazon SES (HTML + text versions)                   │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
                   Your Inbox 📬
```

## 🎨 Email Layout

```
┌────────────────────────────────────────┐
│ Morning Briefing                        │
│ Tuesday, March 4, 2026                  │
├────────────────────────────────────────┤
│                                         │
│  [Purple Gradient Box]                  │
│  ☕️ Fun, Engaging Intro                │
│                                         │
├────────────────────────────────────────┤
│                                         │
│  [Golden Box]                           │
│  📋 Executive Summary:                  │
│  What matters today across all topics   │
│                                         │
├────────────────────────────────────────┤
│                                         │
│  🤖 AI & MACHINE LEARNING               │
│  ┌──────────────────────────────────┐  │
│  │ • Article Title                   │  │
│  │   Witty, informative summary...   │  │
│  └──────────────────────────────────┘  │
│                                         │
│  🔌 API DESIGN                          │
│  ┌──────────────────────────────────┐  │
│  │ • Article Title                   │  │
│  │   Engaging summary...             │  │
│  └──────────────────────────────────┘  │
│                                         │
│  [...more topics...]                    │
└────────────────────────────────────────┘
```

## ⚙️ Configuration

### Customize Topics

Edit `config/topics.yaml`:

```yaml
topics:
  - name: "Your Topic Here"
    description: "What you want to know about"
```

### Change Schedule

Default: 6 AM EST (11:00 UTC). Modify in `config/topics.yaml`:

```yaml
briefing:
  schedule: "cron(0 11 * * ? *)"  # UTC time
```

### Adjust Article Limits

```yaml
briefing:
  max_articles_per_topic: 8           # Articles to collect per topic
  search_results_per_topic: 15        # Search results to consider
```

## 🔐 Security & Privacy

- ✅ **No secrets in code** - All sensitive data in AWS Parameter Store
- ✅ **Encrypted at rest** - SecureString parameters use KMS
- ✅ **IAM best practices** - Least privilege permissions
- ✅ **No data storage** - Stateless Lambda execution
- ✅ **HTTPS everywhere** - All API calls encrypted in transit

## 💰 Cost Breakdown

Estimated monthly cost: **~$5-6**

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 30 invocations × 30s avg | ~$0.20 |
| Bedrock | ~200 API calls/day (Claude) | ~$3.00 |
| Tavily AI | 180 searches (6 topics × 30 days) | Free tier |
| SES | 30 emails | ~$0.10 |
| SSM | 3 parameters | Free |
| EventBridge | 30 rule executions | Free |

## 🛠️ Development

### Run Tests

```bash
poetry run pytest
poetry run pytest --cov=personal_briefing
```

### Lint & Type Check

```bash
poetry run ruff check .
poetry run ruff format .
poetry run mypy src/
```

### Local Testing

```bash
# Set environment variables
export TAVILY_API_KEY="your-key"
export RECIPIENT_EMAIL="your@email.com"
export SENDER_EMAIL="sender@email.com"

# Run handler locally
poetry run python -c "from src.personal_briefing.handler import lambda_handler; lambda_handler({}, None)"
```

## 📝 Project Structure

```
personal-briefing/
├── config/
│   └── topics.yaml              # Topics configuration (template)
├── cdk/
│   ├── app.py                   # CDK entry point
│   └── stacks/
│       └── briefing_stack.py    # Lambda, EventBridge, IAM
├── src/personal_briefing/
│   ├── __init__.py              # Config loader
│   ├── collector.py             # Tavily AI search
│   ├── summarizer.py            # Bedrock Claude summaries
│   ├── emailer.py               # SES email formatting
│   ├── handler.py               # Lambda entry point
│   └── models.py                # Pydantic data models
├── tests/                       # Pytest tests (92% coverage)
├── scripts/
│   └── build-lambda.sh          # Lambda deployment package builder
├── pyproject.toml               # Poetry dependencies
└── README.md
```

## 🔄 CI/CD with GitHub Actions

The repo includes a GitHub Actions workflow for automated testing and deployment.

### Setup GitHub Actions (Optional)

If you want auto-deployment on push to `main`:

1. **Create OIDC Provider** in AWS (if not already done):
   ```bash
   ./scripts/setup-github-oidc.sh
   ```

2. **Add GitHub Secret**:
   - Go to repo Settings → Secrets → New repository secret
   - Name: `AWS_ROLE_ARN`
   - Value: `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsDeployRole`

3. **Push to main** and watch it deploy automatically! 🚀

The workflow:
- ✅ Runs tests, linting, and type checking on every PR
- ✅ Deploys to AWS on push to `main` branch
- ✅ Uses OIDC (no long-lived AWS credentials needed)

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- **Tavily AI** - Excellent web search API
- **Amazon Bedrock** - Claude 3.5 Sonnet is incredible
- **AWS CDK** - Infrastructure as Code done right
- **Poetry** - Python dependency management
- **Community** - Thanks to all contributors!

## 🐛 Troubleshooting

### Emails Going to Spam

**Solution:** The app now includes:
- Plain text version (required by spam filters)
- Proper Reply-To headers
- Clean HTML structure

If still in spam, add sender to your contacts or mark as "Not Spam"

### Bedrock Access Denied

**Solution:** Enable Claude models in AWS Console:
```
Bedrock → Model Access → Request Access → Claude 3.5 Sonnet
```

### Lambda Timeout

**Solution:** Increase timeout in `cdk/stacks/briefing_stack.py`:
```python
timeout=Duration.minutes(10),  # Increase if needed
```

### No Articles Found

**Solution:** Check Tavily API key:
```bash
aws ssm get-parameter --name "/personal-briefing/tavily-api-key" --with-decryption --region us-east-2
```

## 📬 Questions?

Open an issue on GitHub or reach out to the community!

---

**Made with ☕ and 🤖 by developers who read too much tech news**
