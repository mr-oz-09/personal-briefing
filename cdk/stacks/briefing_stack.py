"""CDK stack for Personal Briefing infrastructure."""

from pathlib import Path

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    Stack,
)
from aws_cdk import (
    aws_events as events,
)
from aws_cdk import (
    aws_events_targets as targets,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from aws_cdk import (
    aws_logs as logs,
)
from constructs import Construct


class PersonalBriefingStack(Stack):
    """Lambda + EventBridge + IAM for daily news briefing."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(scope, construct_id, **kwargs)

        project_root = Path(__file__).parent.parent.parent
        lambda_package = project_root / "build" / "lambda-package.zip"

        # Lambda function from pre-built package
        briefing_fn = lambda_.Function(
            self,
            "BriefingFunction",
            function_name="personal-briefing",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="personal_briefing.handler.lambda_handler",
            code=lambda_.Code.from_asset(str(lambda_package)),
            timeout=Duration.minutes(5),
            memory_size=512,
            environment={
                "LOG_LEVEL": "INFO",
                "PYTHONPATH": "/var/task",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Generates and sends daily news briefing",
        )

        # SSM Parameter Store read permission
        briefing_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/personal-briefing/*",
                ],
            )
        )

        # Bedrock invoke permission
        briefing_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-*",
                ],
            )
        )

        # SES send permission
        briefing_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ses:SendEmail", "ses:SendRawEmail"],
                resources=["*"],
            )
        )

        # EventBridge daily schedule (6 AM EST = 11:00 UTC)
        rule = events.Rule(
            self,
            "DailySchedule",
            schedule=events.Schedule.cron(
                minute="0",
                hour="11",
                month="*",
                week_day="*",
                year="*",
            ),
            description="Trigger daily briefing at 6 AM EST",
        )
        rule.add_target(targets.LambdaFunction(briefing_fn))

        # Outputs
        cdk.CfnOutput(self, "FunctionName", value=briefing_fn.function_name)
        cdk.CfnOutput(self, "FunctionArn", value=briefing_fn.function_arn)
