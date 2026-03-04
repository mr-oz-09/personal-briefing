#!/usr/bin/env python3
"""CDK application for Personal Briefing system."""

import aws_cdk as cdk
from stacks.briefing_stack import PersonalBriefingStack

app = cdk.App()

PersonalBriefingStack(
    app,
    "PersonalBriefingStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-2",
    ),
    description="Daily AI-powered news briefing via Bedrock and SES",
)

app.synth()
