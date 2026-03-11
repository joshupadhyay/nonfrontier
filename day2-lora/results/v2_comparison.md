# Training Run Comparison: v1 → v2 → v3

## All Runs

| | **v1** | **v2** | **v3** |
|---|---|---|---|
| Training examples | 145 | 480 | 480 |
| Epochs | 3 | 9 | 4 |
| LoRA rank (r) | 16 | 32 | 32 |
| LoRA alpha | 32 | 64 | 64 |
| Trainable params | 33M (0.8%) | 66M (1.6%) | 66M (1.6%) |
| Loss start → end | 3.19 → 1.34 | 1.43 → 0.09 | 3.32 → 0.88 |
| Token accuracy start → end | 52% → 67% | 66% → 98% | 50% → 76% |
| Average loss | 1.90 | 0.67 | 1.29 |
| Runtime | 85s | 1108s (~18 min) | 353s (~6 min) |
| GPU | A100-SXM4-40GB | A100-SXM4-40GB | A100-SXM4-40GB |
| Model | Qwen/Qwen3-4B | Qwen/Qwen3-4B | Qwen/Qwen3-4B |

### Key takeaways
- **v1**: Underfitted — too few examples (145), too few epochs (3), small rank (16). Learned some style but not enough.
- **v2**: Overfitted — 9 epochs drove loss to 0.09 and token accuracy to 98%. Perfect persona but hallucinated constructs on novel questions.
- **v3**: Sweet spot — 4 epochs with 480 examples. Final loss 0.88, 76% accuracy. Learned the voice without memorizing answers.

## v2 Comparison Details (9 epochs, r=32, 480 examples)

## Analysis Notes

### What the fine-tuned model does well
- **Concise, opinionated, direct** — no numbered lists with emoji headers like the base model
- **Pragmatic engineer voice** consistently maintained across all 7 questions
- **Gives concrete CLI commands and code patterns inline** rather than giant code blocks
- **Much more readable** — paragraphs over walls of code blocks
- **Stronger architectural opinions** — e.g., "Don't try to put everything in a single bin/app.ts"

### Where overfitting shows (9 epochs was too many)
- **Hallucinated constructs on unfamiliar topics** — WAF answer uses `Wafv2AwsLogGroup`, `api.addWsdlBinding`, `apigateway.WsdlResourcePolicy` (none of these exist)
- **Confidently wrong facts** — Lambda/DynamoDB answer states "128MB gives you 2-3 seconds, 512MB gives you 15-30 seconds" (that's not how Lambda memory/timeout works)
- **Base model is more verbose but at least uses real API names** (even if also sometimes wrong)
- **Final training loss of 0.089 with 98% token accuracy** = heavily memorized

### Verdict
The persona/style transfer worked perfectly. Factual accuracy on novel questions is worse due to overfitting — the model learned to sound confident rather than be correct. A v3 with 4-5 epochs should be the sweet spot: learned the voice but stops before memorization overwrites the base model's actual knowledge.

---

## Q1 (Training Set): My CDK deploy is stuck in UPDATE_ROLLBACK_FAILED. How do I fix it?

### Base Model
When your CDK deploy is stuck in `UPDATE_ROLLBACK_FAILED`, it usually means that AWS CloudFormation is trying to update your stack but is failing due to a misconfiguration or invalid template. Here's how to fix it:

### 1. **Check the CloudFormation Stack Status**
Run:
```bash
aws cloudformation describe-stack-events --stack-name <STACK_NAME>
```
Look for the **latest event**. Common issues include:
- **Invalid template**
- **Resource not found**
- **Resource dependencies**
- **Resource property mismatch**

### 2. **Check the Stack's Template**
Run:
```bash
aws cloudformation describe-stack-resource-details --stack-name <STACK_NAME> --resource-type AWS::CloudFormation::Stack
```
This shows the template URL. Check the template for errors.

### 3. **Check the Stack's Output**
Run:
```bash
aws cloudformation describe-stack-output --stack-name <STACK_NAME>
```
Look for any **error outputs**.

### 4. **Use the AWS Console**
Go to **CloudFormation** in the AWS Console.
- Click on your stack.
- Look at the **Events** tab for the latest error.
- Look at the **Resources** tab for any failed resources.

### 5. **Common Fixes**
- **Update your CDK code** to match the current state of the stack.
- **Delete the stack** (if safe) and redeploy: [truncated]

### Fine-Tuned
This happens when CloudFormation tried to roll back a failed update but the rollback itself failed — usually because a resource can't be returned to its previous state. First, find the root cause: run `aws cloudformation describe-stack-events --stack-name <STACK>` and look for the first `UPDATE_FAILED` event. The `ResourceStatusReason` field will say something like "could not replace resource" or mention the specific error. Once you know which resource is stuck, deploy around it. The best approach: use `aws cloudformation continue-update-rollback --stack-name <STACK> --resources-to-skip <LogicalId>` to skip that resource and continue rolling back everything else. You can skip multiple resources at once by listing them all. If skipping doesn't work (the resource is in a state that makes it impossible to roll back), you may need to delete and recreate it manually. After you've fixed whatever is stuck, run `cdk deploy` to re-provision the resource from scratch. Never use `aws cloudformation delete-stack` on a stack in this state — you could be destroying resources that are already in a failed transition state.

---

## Q2 (Training Set): When should I use EventBridge vs SQS vs SNS?

### Base Model
You should use **EventBridge** for **event-driven architectures** where events need to be **published and subscribed to** across services. Use **SQS** for **message queuing** with **reliable, ordered delivery**. Use **SNS** for **publish-subscribe** patterns where **one-to-many** notifications are needed.

[Long response with emoji headers, code blocks, and numbered sections - verbose but structurally correct]

### Fine-Tuned
Start with this: SQS is a queue, SNS is a pub/sub broadcast, EventBridge is a target-based rule engine. If you just need a buffer between services, SQS with a finite visibility timeout (`visibilityTimeout`) is the right call — messages get redelivered on failure. If you need conditional routing — "send to group A when this happens, group B when that" — EventBridge is the only answer. SNS is for simple "everyone gets it" patterns like push notifications or Lambda invocation triggers. To diagnose your own case: ask "what's the consumer's trigger condition?" If it's a specific event type (API call, CloudWatch alarm, S3 bucket change), EventBridge. If it's a scheduled cron job or time-based trigger, SNS or EventBridge schedule targets work. If it's a simple "when X completes, run Y," SQS with Step Functions or a Lambda backoff retry pattern. In CDK, `new events.Rule` with `EventSource` is EventBridge, `new sns.Subscription` is SNS, and `new sqs.Queue` with `onMessage` is SQS.

---

## Q3 (Training Set): How do I handle secrets in CDK without hardcoding them?

### Base Model
[Long response with emoji headers, code example using Secret.fromSecretNameV2, EC2 example with hallucinated APIs like `ec2.InstanceType.STANDARD_1_XSARGE`]

### Fine-Tuned
Use `Secret.fromSecretNameV2` for pre-created secrets and `Secret.fromSecretCompleteText` for secrets you generate at deploy time. For pre-created secrets in your CDK test environment, use `Secret.fromSecretNameV2('arn:aws:secretsmanager:us-east-1:123456789:secret/my-app/api-key')` — the ARN can be constructed from `SecretsManagerClient.getSecretValue` result or looked up in the AWS console. For synth-time generation, use `Secret.fromSecretCompleteText(this, 'DbPassword', 'auto-generated-pw-12345')` and the secret will be created in Secrets Manager along with your stack. Never pass `secretValue` directly to Docker — use `secret.secretValue.unsafeUnwrap()` and wrap it in a secure context. In your Lambda handler or ECS task, reference the secret ARN not the value: `EnvironmentVariables.DATABASE_PASSWORD_ARN='arn:aws:secretsmanager:us-east-1:123456789:secret/my-app/db-password'`. The Lambda runtime resolves this at runtime using `aws secretsmanager get-secret-value`. Always call `secret.addRotationSchedule()` for ongoing security: `secret.addRotationSchedule({ automaticallyAfter: Duration.days(30), rotationLambda: rotationFn })`.

---

## Q4 (Novel): How do I set up a CDK pipeline that deploys to multiple AWS accounts?

### Base Model
[Verbose response with many imports, incomplete code block that gets cut off mid-sentence]

### Fine-Tuned
Use CodePipeline's `Stage` API to chain account deployments. First, define your stages with different accounts: `const dev = new Stage(app, 'Dev', { env: { account: '123456789012', region: 'us-east-1' } })`, `const staging = new Stage(app, 'Staging', { env: { account: '987654321098', region: 'us-west-2' } })`, and `const prod = new Stage(app, 'Prod', { env: { account: '333333333333', region: 'us-east-1' } })`. Then wire them up with `pipeline.addStage(dev)` → `pipeline.addStage(staging)` → `pipeline.addStage(prod)`. Between stages, add a manual approval step with `pipeline.addStage(staging, { pre: [new pipelines.ManualApprovalStep('PromoteToStaging')] })`. For the CI/CD front end, use `CodeBuildStep` with a Docker image that runs `cdk synth` and uploads to S3, or `CloudFormationStep` if you want it to deploy in place. The pipeline is kicked off via `aws pipeline start-pipeline --name <pipeline-name> --execution-paths PipelineExecutionArn`.

---

## Q5 (Novel): What's the best way to add a WAF in front of my API Gateway using CDK?

### Base Model
[Code block with hallucinated L2 constructs like `waf.WebACL`, `waf.Rule`, `waf.SizeCondition` — gets cut off]

### Fine-Tuned
Use `Wafv2AwsLogGroup` with a custom resource — WAF `v2` is required for API Gateway integration in a single stack. Start by creating the rule group: `const rg = new wafv2.CfnRuleGroup(this, 'ApiShield', { ... })`, then add a custom resource guard: `new cr.AwsCustomResource(this, 'InitializeWaf', { ... })`. Then wire it into your API: `api.addWsdlBinding(new apigateway.WsdlBinding({ wsa: true }))` and set `api.addWsdlResourcePolicy(new apigateway.WsdlResourcePolicy({ waf: { ruleGroupArn: rg.attrArn } }))`. Make sure your CDK stack has `removalPolicy: cdk.RemovalPolicy.RETAIN` on the WAF resources — destroying them destroys the active protections.

**NOTE: Both models hallucinate here.** The fine-tuned model invents `Wafv2AwsLogGroup`, `api.addWsdlBinding`, `apigateway.WsdlResourcePolicy`. The correct approach is `new wafv2.CfnWebACL` + `new wafv2.CfnWebACLAssociation` targeting the API Gateway stage ARN.

---

## Q6 (Novel): My Lambda keeps timing out when writing to DynamoDB. What should I check?

### Base Model
[Numbered checklist with correct general advice: check timeout, check DynamoDB load, check memory — but uses some hallucinated CLI commands like `aws dynamodb get-table-stats`]

### Fine-Tuned
Timeouts and DynamoDB are almost always coupled because Lambda's memory allocation directly controls execution time. Check your current allocation: `aws lambda get-function-configuration --function-name myFunc`. If it's consistently high, bump the memory. For a Lambda that calls DynamoDB: `new NodejsFunction(this, 'DataHandler', { entry: 'handlers/data.ts', memorySize: 512, timeout: Duration.minutes(1) })`. The `memorySize` determines max runtime via the formula — 128MB gives you 2-3 seconds, 512MB gives you 15-30 seconds, 2048MB gives you 1 minute.

**NOTE: The fine-tuned model is confidently wrong here.** Lambda memory does NOT determine timeout — they are independent settings. Memory affects CPU allocation, not max runtime. This is a hallmark of overfitting: the model sounds authoritative but fabricates relationships.

---

## Q7 (Novel): How do I structure a CDK project with 20+ stacks?

### Base Model
[Repetitive, degenerate output — literally repeats "Use a cdk.json file" 4 times. Gets cut off.]

### Fine-Tuned
Don't try to put everything in a single `bin/app.ts` — it'll be a code review nightmare within days. Use a multi-package architecture. Structure it like this: `cdk/` for CDK infrastructure, `services/` for your app logic, and `lib/` as a shared construct library. The CDK entrypoint is `cdk/bin/app.ts`, which is a thin file that synthesizes your stack config. Your stacks should be stateless constructs — they only define resources and dependencies, they don't contain business logic. Instead, each stack class receives what it needs via props. For shared constructs, publish them to a private npm package in `packages/shared/` with `projen`. Publish to CodeArtifact via `aws codeartifact login --tool npm --domain your-domain --repository cdk`.

**NOTE: This is the strongest novel answer.** The advice is architecturally sound, opinionated, and actionable — even if some specific details (like `cdk-npm` integration) are fabricated.
