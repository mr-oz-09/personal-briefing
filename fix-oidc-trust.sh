#!/bin/bash

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create proper trust policy with session name
cat > /tmp/github-trust-fixed.json << POLICY
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
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:kennymrozjr/personal-briefing:ref:refs/heads/main"
        }
      }
    }
  ]
}
POLICY

# Update the role
aws iam update-assume-role-policy \
  --role-name GitHubActionsDeployRole \
  --policy-document file:///tmp/github-trust-fixed.json

echo "Trust policy updated - should now work!"
