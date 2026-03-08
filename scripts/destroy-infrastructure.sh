#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}⚠️  WARNING: This will destroy ALL infrastructure!${NC}"
echo ""
echo "This will delete:"
echo "  - Lambda function: personal-briefing"
echo "  - EventBridge schedule rule"
echo "  - CloudWatch log groups"
echo "  - IAM roles and policies"
echo ""
echo -e "${YELLOW}Parameter Store values will NOT be deleted.${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
echo

if [[ ! $REPLY =~ ^yes$ ]]; then
    echo -e "${GREEN}Aborted. No changes made.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}🗑️  Destroying infrastructure...${NC}"
echo ""

cd "$(dirname "$0")/../cdk"

# Run CDK destroy
if poetry run cdk destroy --force; then
    echo ""
    echo -e "${GREEN}✅ Infrastructure destroyed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}To delete Parameter Store values, run:${NC}"
    echo ""
    echo "  aws ssm delete-parameter --name /personal-briefing/tavily-api-key --region us-east-2"
    echo "  aws ssm delete-parameter --name /personal-briefing/recipient-email --region us-east-2"
    echo "  aws ssm delete-parameter --name /personal-briefing/sender-email --region us-east-2"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Failed to destroy infrastructure${NC}"
    exit 1
fi
