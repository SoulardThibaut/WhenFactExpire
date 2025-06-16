# When Facts Expire: A Benchmark for Temporal Fact Validation

This repository contains the resources and methodology for creating and using the Temporal Knowledge Graph (TKG) benchmark introduced in the paper, "When Facts Expire: Benchmarking Temporal Validity in Knowledge Graphs."

This benchmark is designed to evaluate a model's ability to validate facts within a specific temporal context. Unlike traditional KG completion tasks that focus on predicting missing entities or relations, this work focuses on assessing the temporal plausibility of a given fact.
Overview

The core challenge this benchmark addresses is that the validity of many facts is time-dependent. For example, the fact (Barack Obama, HeadOfState, USA) is only true for the interval [2009-01-20, 2017-01-20]. This benchmark provides a systematic way to test a model's understanding of such temporal constraints by providing facts where only the temporal component has been intentionally corrupted.
Creating the Benchmark Data

The process of generating the benchmark involves several steps, from extracting raw data from Wikidata to generating carefully constructed negative samples.
1. Data Extraction

    Source: A local dump of Wikidata (specifically, the version from May 25th, 2023).

    Process: Temporally contextualized facts are retrieved using two main types of queries:

        Facts with a specific timestamp, using the Point In Time (P585) property.

        Facts with a duration, using Start Time (P580) and/or End Time (P582).

    Result: This initial extraction yields millions of raw temporal facts.

2. Graph Preprocessing and Sampling

To create datasets with varying characteristics, the raw graph is filtered and processed based on several criteria. This allows for testing models across different scales, densities, and temporal scopes.
Configuration Options:

    Temporal Scope:

        Reduced Scope [1900, 2023]: A dense and consistent set of modern historical facts.

        Full Scope [-1000, 2023]: A sparser dataset with facts spanning from ancient to modern history.

    Graph Size & Density (Connectivity Filter N): The graph is filtered to ensure that every remaining entity is connected to at least N other unique entities.

        Extra-Small (N=15): A compact, highly-connected graph for rapid prototyping.

        Small (N=10): A dense graph for testing core temporal reasoning.

        Medium (N=8): A balanced setting between size and connectivity.

        Large (N=4): A large and more sparse graph to test generalization.

    Temporal Granularity:

        Year Level: Timestamps are reduced to year-level precision, increasing the usage of each unique timestamp. This tests a model's ability to reason about macro-level event sequences.

        Day-Month-Year Level: Presents a significant challenge with a large and sparse set of unique timestamps, testing model scalability and precision.

3. Negative Sample Generation

The key to this benchmark is its negative sampling strategy, which creates plausible-but-false temporal facts.

    Identify Context: For a true fact (s, p, o, τ), we first gather all other true facts for the same subject s and predicate p. This forms a timeline of activity for that (s, p) pair.

    Define Search Window: A plausible time window for creating a false fact is defined. It starts with the "lifespan" of the subject s (its earliest to latest appearance in the KG) and extends it by 10% to create a more challenging task.

    Generate Negative Sample: The algorithm identifies empty "gaps" in the (s, p) timeline within the search window. It then randomly generates a new time interval τ_n within one of these gaps to create the negative sample (s, p, o, τ_n).

    Maintain Balance: The final dataset maintains a strict 1:1 ratio of positive to negative samples. If no temporal gap exists for an (s, p) pair to generate a negative sample, the original positive fact is removed from the dataset.

4. Semantic Information Integration

To enable more sophisticated reasoning, the benchmark is enriched with:

    Ontological Information: Class hierarchies for logical reasoning.

    Datatype Properties: Literal values, such as a person's birthDate, which can be used to cross-validate other facts. For instance, a model could refute (Joe Biden, HasRole, US_President) for a time in the 1960s by calculating his age and finding it inconsistent with the role's requirements.

## Using the Benchmark Data

The primary task for this benchmark is Temporal Fact Validation.
Evaluation Task

Given a full quadruple (s, p, o, τ), a model must predict whether the fact is plausible within the given temporal context τ. This is a binary classification task (true/false).
Evaluation Protocol

Since many TKG models are designed for link prediction (ranking), they must be adapted for this validation task.

    Scoring: Use the model's scoring function to get a plausibility score for the full input fact (s, p, o, τ).

    Classification: Apply a threshold to the score to classify the fact as temporally valid or invalid.

    Metrics: For facts with time intervals, metrics like Intersection over Union (IoU) can be used to compare a model's predicted interval with the ground truth to determine correctness before applying the classification threshold.

The benchmark is explicitly designed to challenge models that learn a unique embedding for each timestamp, as they may struggle with the high temporal cardinality of the Day-Month-Year settings.
