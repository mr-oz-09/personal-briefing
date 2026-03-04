#!/bin/bash

set -e

echo "========================================="
echo "GitHub OIDC Setup for AWS"
echo "========================================="
echo ""

# Get AWS Account ID
echo "Getting AWS Account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✓ Account ID: $ACCOUNT_ID"
echo ""

# Create trust policy
echo "Creating trust policy..."
cat > /tmp/github-actions-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:kennymrozjr/personal-briefing:*"
        }
      }
    }
  ]
}
EOF
echo "✓ Trust policy created"
echo ""

# Check if role exists
echo "Checking if GitHubActionsDeployRole exists..."
if aws iam get-role --role-name GitHubActionsDeployRole &> /dev/null; then
    echo "⚠ Role already exists, updating trust policy..."
    aws iam update-assume-role-policy \
      --role-name GitHubActionsDeployRole \
      --policy-document file:///tmp/github-actions-trust-policy.json
    echo "✓ Trust policy updated"
else
    echo "Creating new role..."
    aws iam create-role \
      --role-name GitHubActionsDeployRole \
      --assume-role-policy-document file:///tmp/github-actions-trust-policy.json
    echo "✓ Role created"

    echo "Attaching policies..."
    aws iam attach-role-policy \
      --role-name GitHubActionsDeployRole \
      --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

    aws iam attach-role-policy \
      --role-name GitHubActionsDeployRole \
      --policy-arn arn:aws:iam::aws:policy/IAMFullAccess
    echo "✓ Policies attached"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""

# Get the role ARN
ROLE_ARN=$(aws iam get-role \
  --role-name GitHubActionsDeployRole \
  --query Role.Arn \
  --output text)

echo "Add this to GitHub Secrets:"
echo ""
echo "Secret Name: AWS_ROLE_ARN"
echo "Secret Value:"
echo ""
echo "    $ROLE_ARN"
echo ""
echo "Go to: https://github.com/kennymrozjr/personal-briefing/settings/secrets/actions"
echo ""
echo "Also add:"
echo "Secret Name: TAVILY_API_KEY"
echo "Secret Value: tvly-your-api-key-here"
echo ""
