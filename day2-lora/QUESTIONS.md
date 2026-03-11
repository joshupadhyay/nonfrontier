# AWS & CDK Fine-Tuning Questions

Seed questions for generating synthetic training data. Target: 5 variations per question.

## Debugging & Troubleshooting

1. My SQS queue isn't receiving messages from my SNS topic. Why might that be?
2. My CDK deploy is stuck in UPDATE_ROLLBACK_FAILED. How do I fix it?
3. Lambda can't reach my RDS instance in the same VPC. What's wrong?
4. My API Gateway returns 502 — where do I look?
5. My CDK failed because a resource already exists. How do I import this resource or adjust this?
6. My CloudWatch logs aren't showing up for my Lambda — what's wrong?
7. CDK is replacing my resource instead of updating it in place, causing a rollback. Which resource properties trigger replacement vs. in-place update?

## CDK Patterns & Best Practices

7. How do I reference resources across stacks in CDK?
8. How do I migrate resources from one CDK stack to another?
9. How do I translate a lambda deployment from CloudFormation to CDK?
10. How do I handle secrets/env vars in CDK without hardcoding them?
11. How do I lint my CDK before I deploy it?
12. Is it better to deploy this application all in one stack, or multiple stacks? When is one approach better than the other?
13. What are best practices for tagging AWS stacks so I can find them from GitHub, or find resources related to each other?
14. How do I deploy an S3 bucket with a specific encryption key?

## Architecture Decisions

15. When should I use Aurora Serverless vs a normal relational database?
16. When should I use EventBridge, SQS, or SNS?
17. Should I use a monolithic Lambda or split into multiple functions?
18. When should I use Lambda@Edge?
19. What's a good pattern for deploying Docker images to AWS?
20. Modal is a serverless GPU platform. When might serverless GPUs be preferred over AWS Batch or scheduling with EC2 instances?

## Operational

21. How do I set log levels in a Lambda so I can adjust them dynamically without redeploying?
22. What permissions do I need to read and write to my S3 bucket?
23. I have a publicly-facing EC2 instance. How do I add DNS? What type of records can I use?
24. Give me the AWS CLI command for listing all logs from this S3 bucket in the past hour.
25. How do I set up a dead letter queue for failed Lambda invocations?
26. Given the software in this application, what should I set my Lambda timeout to? What's a good rule of thumb or benchmark?
27. What IAM roles exist by default in AWS that work well here?
28. How can I set up a SCIM connector / authorization? Are there any AWS resources to support this for an EC2 instance?
