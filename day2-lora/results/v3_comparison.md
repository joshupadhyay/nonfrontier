# v3 Comparison: Base vs Fine-Tuned (4 epochs, r=32, 480 examples)

## Analysis Notes

### Improvements over v2
- **Less hallucination on novel questions** — WAF answer still invents some APIs but uses real ones too (`wafv2.CfnRuleGroup` is correct)
- **Lambda/DynamoDB answer is much better** — correctly identifies IAM permissions, throttling, and timeout as separate issues (v2 conflated memory with timeout)
- **CDK pipeline answer** uses real constructs (`pipelines.CodePipeline`, `pipelines.ShellStep`, `ManualApprovalStep`)
- **20+ stacks answer** gives real architectural advice: domain folders, SSM for cross-stack refs, CDK Aspects for cross-cutting concerns

### Remaining issues
- Still some fabricated APIs (WAF: `api.addWsdlStage`, Lambda: `aws dynamo-db get-table-statistics`)
- Some incorrect claims (Lambda "hard 3-second timeout for Python" is wrong — default is 3s but configurable)
- EventBridge cost claim ("SNS/SQS costs $0.50-2.00 per event") is wildly wrong

### Style comparison
- v3 fine-tuned responses are consistently more concise and opinionated than base
- Base model tends toward numbered lists with emoji headers and verbose code blocks
- Fine-tuned model gives paragraph-style answers with inline code references
- The "pragmatic engineer" voice comes through clearly without being as aggressively confident as v2

### Verdict
v3 is the best run. 4 epochs hits the sweet spot: the model learned the persona and communication style without memorizing training answers. Novel question quality improved significantly over v2 — real constructs appear more often, and the advice is architecturally sounder even when specific API names are wrong.

---

## Q1 (Training Set): My CDK deploy is stuck in UPDATE_ROLLBACK_FAILED. How do I fix it?

### Base Model
When your CDK deployment is stuck in UPDATE_ROLLBACK_FAILED, it usually means that the stack was in a state where it couldn't be updated due to a conflict with existing resources. Here's how to fix it:

1. Check the CloudFormation stack status: `aws cloudformation describe-stack-events --stack-name <STACK_NAME>`
2. Check the stack's status: `aws cloudformation describe-stacks --stack-name <STACK_NAME>`
3. Delete the stack (if safe): `aws cloudformation delete-stack --stack-name <STACK_NAME>`
4. Use `cdk destroy` or `cdk --force` to redeploy

[Verbose, numbered list approach. Suggests deleting the stack as a primary fix — dangerous advice.]

### Fine-Tuned
You need to manually fix the underlying resource failure. First, identify which resource is causing the problem by running `aws cloudformation describe-stack-events --stack-name <STACK>` and look for the first event with status `UPDATE_FAILED`. Then check the resource's last state with `aws cloudformation describe-stack-resource --stack-name <STACK> --logical-id <LOGICAL-ID>`. Common causes: a resource was deleted from AWS while CloudFormation still expected it, a resource parameter is invalid, or a resource already exists with a different configuration. For example, if a DynamoDB table was deleted, you'll need to recreate it manually before running `aws cloudformation continue-update-rollback`. Once the rollback completes, redeploy normally. If you're deploying to production, consider adding `removalPolicy: RemovalPolicy.RETAIN` to resources that shouldn't be deleted during rollbacks.

**Quality: Excellent.** Correct diagnosis approach, mentions `continue-update-rollback`, warns about production. Much better than base.

---

## Q2 (Training Set): When should I use EventBridge vs SQS vs SNS?

### Base Model
[Standard summary table approach with emoji headers. Correct at a high level but generic.]

### Fine-Tuned
EventBridge is your default. Use it for every event-driven pattern unless you have a specific reason to use SNS/SQS. EventBridge routes events directly to targets by topic: `new events.Rule(this, 'ProcessOrder', { eventPattern: { source: 'orders', detailType: 'placed' }, targets: [new targets.SqsQueue(queue)] })`. This is cheaper, faster, and more reliable than SNS fan-out. SQS is only useful when you need to batch, filter, or process events in a queue before routing them. SNS is only useful for fan-out to non-EventBridge consumers — like HTTP endpoints, email, or legacy systems.

**Quality: Good voice, debatable opinion.** "EventBridge is your default" is a strong take. Cost claim is wrong ($0.50-2.00 per event for SNS/SQS is way off — it's fractions of a cent). But the architectural advice is sound.

---

## Q3 (Training Set): How do I handle secrets in CDK without hardcoding them?

### Base Model
[Uses `Secret.fromSecretNameV2` correctly. Includes EC2 example. Verbose with emoji headers.]

### Fine-Tuned
Use `SecretsManager.Secret.fromSecretNameV2()` for production and `SecretsManager.Secret.fromSecretName()` for dev. Never use `SecretsManager.Secret.fromSecretName()` for production — the v2 variant automatically adds automatic rotation and a default TTL. For dev, use plain SSM parameters.

**Quality: Mixed.** The v1 vs v2 distinction is fabricated (v2 doesn't add automatic rotation). But the dev/prod split advice and SSM recommendation are sound patterns.

---

## Q4 (Novel): How do I set up a CDK pipeline that deploys to multiple AWS accounts?

### Base Model
[Uses hallucinated `cdk-pipeline` import path. Gets cut off mid-code-block.]

### Fine-Tuned
Use `pipelines.CodePipeline` with `pipelines.ShellStep` for synth. Add each stage with `pipeline.addStage(new AppStage(...))`. Deploy with `cdk deploy --all-accounts`. For account-level approval between stages, use `pipeline.addApprovalStep(new pipelines.ManualApprovalStep('Approve'))`.

**Quality: Good.** Uses real constructs (`pipelines.CodePipeline`, `ShellStep`, `ManualApprovalStep`). The `--all-accounts` flag is fabricated but the pattern is correct. Big improvement over v2.

---

## Q5 (Novel): What's the best way to add a WAF in front of my API Gateway using CDK?

### Base Model
[Uses `wafv2.CfnWebACL` (correct L1 construct!) but gets lost in deeply nested statement syntax and truncates.]

### Fine-Tuned
The best way is `new wafv2.CfnRuleGroup()` with a custom rule group. Don't use `Wafv2AccessControlList` — it's deprecated. Wire it up in API Gateway: `api.addWsdlStage('prod', { wafEnabled: true, wafPolicy: wafPolicy })`.

**Quality: Better than v2, still hallucinating.** `CfnRuleGroup` is a real construct (improvement over v2's fully fabricated APIs). But `api.addWsdlStage` is still made up. The correct approach is `CfnWebACL` + `CfnWebACLAssociation`.

---

## Q6 (Novel): My Lambda keeps timing out when writing to DynamoDB. What should I check?

### Base Model
[Correct general checklist: timeout, DynamoDB capacity, region, IAM, concurrency. Verbose but accurate.]

### Fine-Tuned
Three things in order. First, check your execution role — IAM permissions. Second, check DynamoDB throttling limits. Third, check actual execution time. Lambda has a hard 3-second timeout for Python and 15-second for Node.js.

**Quality: Much better than v2, still has errors.** Correctly identifies IAM, throttling, and timeout as separate issues (v2 conflated memory with timeout). But "hard 3-second timeout for Python" is wrong — 3s is the default, not a hard limit. The `aws dynamo-db get-table-statistics` CLI command is fabricated.

---

## Q7 (Novel): How do I structure a CDK project with 20+ stacks?

### Base Model
[Gives a reasonable folder structure with `stacks/` by domain. Generic but not wrong.]

### Fine-Tuned
Create a `lib/` folder per domain boundary. Use SSM parameters for cross-stack references instead of direct stack references. Use CDK Aspects for cross-cutting concerns like `removalPolicy: RemovalPolicy.RETAIN`. Keep your app entrypoint small — it's just a factory that constructs stacks, not a runtime app.

**Quality: Excellent.** Architecturally sound advice. SSM for cross-stack refs (avoids export lock-in), Aspects for cross-cutting, thin entrypoint. This is the best novel answer across all runs.
