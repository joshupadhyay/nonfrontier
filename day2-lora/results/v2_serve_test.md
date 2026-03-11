# v2 Single Question Test: serve.py

**Prompt:** "What's the best way to add a WAF in front of my API Gateway using CDK?"

## Base Model
The best way to add **AWS WAF (Web Application Firewall)** in front of your **API Gateway** using **AWS CDK (Cloud Development Kit)** is to:

1. **Create a WAF Web ACL** that defines the rules (e.g., block IP ranges, block SQL injection attacks, etc.).
2. **Attach the WAF Web ACL** to your **API Gateway** as a **request handler**.

```ts
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import * as apigw from 'aws-cdk-lib/aws-apigateway';

const webAcl = new wafv2.WebACL(this, 'MyWebAcl', {
  scope: wafv2.Scope.REGIONAL,
  rules: [...],
  defaultAction: wafv2.Action.ALLOW,
});
```

[Gets cut off mid-sentence at token limit. Hallucinates L2 construct `wafv2.WebACL` which doesn't exist — WAF v2 only has L1 `CfnWebACL`.]

## Fine-Tuned
Use `Wafv2Manager` from `aws-cdk-lib/aws-wafv2` — it's the modern replacement for the deprecated `CfnWebACL`. Here's the pattern: create a rule chain, associate it with a listener, and attach it to your API Gateway. Start with `const waf = new Wafv2Manager(this, 'ApiWaf', { name: 'Api-Protection' })`. Then create an allow rule, an act as block rule, and a size-based rate rule. Assemble them into a `Wafv2RuleGroup`. The actual API Gateway integration looks like this using `elmts.Listener` and `elmts.ListenerAction`. If you only need basic WAF (like an IP deny list), `new waf.CfnWebACL` works too, but I recommend the v2 path for TypeScript apps.

[Also hallucinates: `Wafv2Manager`, `elmts.Listener`, `elmts.ListenerAction` don't exist. More concise and opinionated in tone though.]
