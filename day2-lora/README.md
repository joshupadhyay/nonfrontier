# LoRA

Welcome back! Today is day 2 of messing with models.

## What's LoRA?

We'll be fine-tuning our own model today with LoRA (Low-Rank Adaptation). Instead of training a new model from scratch, we leverage most of a 'base' model and teach it a few new behaviors. This is more cost efficient, produces a model faster, and is much cheaper.

> What's fine-tuning?
> Fine-tuning refers to adjusting a subset of the model weights to adjust select behaviors.

The result: you train maybe 0.5-2% of the total parameters, use a fraction of the memory, and can swap adapters in and out at inference time.


## Why would I fine-tune?

Base models are great for general-purpose tasks. However, a model doesn't really know what your company process is, or what you look like - it just doesn't have enough examples to pull from. Domain-specific tasks, or emphasizing a certain behavior is where fine-tuning becomes more valuable. We can provide additional information and slightly train the model on new information, to greatly help in specific use cases.

Here's a use case from Docker, where they train Gemma 3 to mask [personally identifiable information](https://arc.net/l/quote/uickeynh).

## A Speedy Cloud Developer

At 3M, a big pain point was AWS' CDK. CDK enables developers to deploy infrastructure as code, but is often not prescriptive on best-practices in a company setting. There's little stopping a developer from creating a S3 bucket and turning object encryption off, or creating EC2 instances with an open IP. Our cloud engineering team found ourselves writing class on top of CDK ([our own L2 constructs](https://arc.net/l/quote/jigwamhn)... I guess L2 constructs?). Let's see if we can teach a model CDK best practices, so I can avoid expensive Claude API calls and learn about LoRA!

## 
