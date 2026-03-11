# New Fine-Tuning Questions — Deduplicated

## CDK Structure & Architecture

1. How should I structure a CDK app with stateful resources (databases) vs stateless resources (Lambdas) in separate stacks, and what are the concrete signals for when to split?
2. Why is organizing CDK constructs by business domain superior to organizing by AWS resource type?
3. How do I restructure a CDK app that has grown to 6+ stacks with 25-minute deployments?
4. When should I split a CDK app from a single package into multiple packages or repos vs keeping a monorepo?
5. What is the blast radius risk of putting shared infrastructure and application stacks in the same CDK app?
6. What's the right folder structure for separating CDK infrastructure from Lambda handler code in the same repo?

## Logical IDs & Resource Replacement

7. How do I prevent CDK from replacing my RDS database when I refactor constructs and the logical ID changes?
8. How do I write a CDK unit test that asserts the logical ID of a stateful resource hasn't changed between refactors?
9. My team hardcodes physical resource names so other services can reference them — what problems will this cause when we need to replace an immutable resource, and how do we migrate to generated names?

## CDK Context & Deterministic Synthesis

10. Should I commit cdk.context.json to version control — walk through the AZ rebalance failure scenario that happens when I don't?
11. How do context providers and .fromLookup() prevent non-deterministic synthesis, and what is the correct workflow for refreshing cached context values?
12. My CDK construct reads process.env for configuration — why does it produce different templates on different machines, and at what level should environment variable lookups be confined?

## CDK Aspects & Compliance

13. How do I use CDK Aspects to enforce that all S3 buckets have a removal policy set before deployment?
14. How do CDK Aspects interact with synthesis — can they block cdk deploy if a violation is found?
15. If CDK Aspects can validate security properties across an entire construct tree, when would I still need CloudFormation Guard or SCPs?
16. What combination of SCPs, permissions boundaries, and CDK Aspects should I use for layered security guardrails?

## CDK Nag & CI Gating

17. How do I integrate CDK Nag into my CI pipeline so security violations fail the build, and how does it differ from cfn-nag?
18. What pre-deployment CDK tests should I write that run at synthesis time?

## Parameters, Conditions & Configuration

19. When is it appropriate to use CloudFormation Parameters and Conditions in a CDK app versus handling environment-specific logic entirely in TypeScript/Python at synthesis time?
20. How do I model per-stage configuration so dev uses on-demand and prod uses provisioned — without duplicating stack code?
21. How should CDK apps structure removal policies differently between dev and production stacks?
22. When to use CfnParameter vs CDK context vs environment variables for configuration?

## Shared Construct Libraries

23. How should a platform team structure a shared CDK construct library — monorepo or CodeArtifact versioned package — with release process, ownership, and testing strategy for multiple consuming teams?
24. When building internal "L2.5" compliance constructs that enforce security defaults, how do I balance guardrails with ecosystem compatibility so they don't block third-party constructs?
25. How do I create a CDK template/starter project with pipeline, security defaults, and observability baked in?

## IAM & Permissions

26. Our security team wants all CDK apps to use pre-created IAM roles instead of CDK-generated roles — what are the trade-offs versus grant methods with Permission Boundaries and SCPs?
27. I'm using grant_read_write_data() everywhere — what are the hidden risks of CDK's built-in grant methods for production security?

## Cross-Stack & Cross-Region

28. How do I handle "Export cannot be deleted as it is in use" errors when refactoring cross-stack references?
29. How do I handle cross-region resource dependencies for disaster recovery with CDK?
30. When two CDK constructs share a dependency (e.g., a DLQ), what are the valid ownership patterns?

## CDK Pipelines & Multi-Account

31. How do I set up CDK Pipelines for continuous deployment across dev, staging, and production accounts in AWS Control Tower?
32. How should I set up CDK bootstrap in each target account with cross-account trust policies?
33. Should each developer get their own AWS sandbox account, share a dev account with stack name prefixing, or use a hybrid approach?
34. How should we structure our AWS Control Tower landing zone so developers can iterate freely in sandbox while enforcing guardrails in prod?

## Passing Values & References

35. How do I pass a CDK-generated DynamoDB table name to a Lambda function without hardcoding the physical resource name?
36. When should I use Table.fromArn() vs passing a DynamoDB table reference directly between CDK stacks in the same app?

## L1 Escape Hatches

37. When should I use L1 escape hatches (CfnResource, addOverride, addPropertyOverride) and what's the maintenance burden?
38. How do I add CloudFormation DependsOn between resources when L2 constructs don't create it automatically?

## Custom Resources

39. How do I implement AwsCustomResource to call an AWS API during deployment?
40. Provider framework vs AwsCustomResource — when should I choose each for custom resource lifecycle management?

## Co-location & Code Organization

41. How do I co-locate Lambda function code and its CDK infrastructure definition in the same construct so they version together, and what are the trade-offs vs a monorepo?
42. Why does over-abstracting CDK code with factory methods and dynamic construct generation hurt team readability and production reliability?
43. Why does AWS recommend modeling constructs as classes extending Construct rather than Stack?

## Drift, Rollback & Ops

44. How do you detect and remediate drift between CDK-defined infrastructure and actual AWS state?
45. How do you bring CDK back in sync after a manual console change to a CDK-managed resource?
46. How do you implement a rollback strategy when a CloudFormation stack update fails partway through?
47. How do you implement emergency rollback when the previous CDK code version has already been merged over?
48. What strategies exist for blue-green or canary deployments with CDK-managed Lambdas and API Gateway?

## CDK Diff & Notifier

49. What is the recommended workflow for using cdk diff in CI/CD to gate deployments, and what do the IAM diff symbols mean?
50. How do I set up CDK Notifier on PRs so reviewers can distinguish safe additive changes from dangerous replacements?

## Stack Refactoring & Migration

51. I have a single stack with RDS, Lambda, API GW, DynamoDB — what's the practical migration path to split without replacing the database?
52. How do I add or remove a stack from a multi-stack CDK app without orphaning resources?
53. What is the safest process for refactoring a CDK construct that contains stateful resources?

## Backup & Data Protection

54. How should I handle DynamoDB point-in-time recovery and AWS Backup through CDK?

## Secrets Management

55. How do you safely rotate secrets referenced by CDK stacks without triggering full redeployment?
56. Recommended strategy for managing sensitive config across stages with Secrets Manager and SSM Parameter Store in CDK?

## Observability & Alarms

57. How do I set up automated CloudWatch metrics, alarms, and rollback triggers within CDK constructs?

## Development Workflow

58. How do I use cdk watch for hot-deploying Lambda changes during development?
59. What is the "console-first" approach to CDK development — prototyping in the AWS console before writing CDK code?

## CDK Synthesis & Debugging

60. How do I debug a "Cannot determine scope" error during CDK synthesis?
61. How do I break a circular dependency between two CDK stacks?
62. How do I troubleshoot a CDK deployment that succeeds in synthesis but fails in CloudFormation execution?
63. How do I identify which constructs create redundant resources in a massive CloudFormation template?
64. The CDK docs say synthesis must be side-effect free — what mechanism should I use if I need to run arbitrary code at deployment time?

## Integration Testing

65. How do you structure CDK integration tests that run against deployed stacks in CI?

## Cloud Center of Excellence

66. What is a Cloud Center of Excellence in the CDK adoption context and how should it operate?

## Conditionals Without CfnCondition

67. What is the best way to conditionally deploy resources in CDK without using CfnCondition?
