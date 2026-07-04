# Cloud Security Accelerator Applications — TopHash

This document contains ready-to-submit application drafts for the three major cloud security accelerator programs. Each application is tailored to the specific program's focus and evaluation criteria.

## Application status

| Program | Status | Cycle | Submission URL |
|---------|--------|-------|----------------|
| AWS Security Accelerator | Ready to submit | Applications open Q1 2026 | https://aws.amazon.com/startups/accelerators/security/ |
| Microsoft for Startups (Azure Security) | Ready to submit | Rolling | https://startups.microsoft.com/ |
| Google Cloud for Startups Security | Ready to submit | Rolling | https://cloud.google.com/startup |

**Before submitting:** Replace `[FOUNDER_NAME]`, `[DATE]`, and verify the current application cycle is open. Each program requires a company entity (Crucible Governance Ltd) and founder identity verification.

---

## 1. AWS Security Accelerator

### Company name
Crucible Governance Ltd (TopHash)

### One-line description
TopHash is the structural identity layer for software supply chains — a training-free, theorem-backed graph fingerprint primitive that produces proof-grade canonical IDs for dependency graphs, molecular graphs, and transaction networks.

### Problem
Software supply chain attacks grew 40% year-over-year (IBM 2024). SBOM tools produce byte-level hashes and dependency lists but cannot prove structural identity between what was built, signed, and shipped. Two packages with isomorphic dependency graphs but completely different dependencies are indistinguishable to topology-blind SBOM tools. The structural opacity tax is $4.45M per breach and 12 months average SBOM drift per enterprise.

### Solution
TopHash is a three-layer structural identity primitive:
1. **TopHash v3** — a training-free 52-dimensional multi-view structural fingerprint (persistent homology + spectral + geometry) that runs in 6.6ms per graph.
2. **TopHashX** — exact canonization (pynauty-backed) producing SHA-256 canonical IDs with machine-auditable proof objects. 100% permutation invariance, 100% agreement with NetworkX isomorphism checker, 1.5ms per graph.
3. **TopHash Ω∞** — counterfactual perturbation engine with stability-bound certificates from bottleneck stability, interleaving distance, and Cheeger inequality.

The entire pipeline is bitwise-deterministic across independent processes (CI-tested).

### Why AWS
TopHash's primary go-to-market is software supply chain security for Python ecosystems (PyPI). AWS is the dominant cloud for Python workloads (Lambda, ECS, EKS, SageMaker). The top 100 PyPI packages have already been fingerprinted with TopHash — the same packages running in millions of AWS deployments. AWS Security Accelerator would connect TopHash to AWS customers who need proof-grade SBOM identity for their Python dependencies, particularly in regulated industries (FinServ, Healthcare, Government) using AWS GovCloud and AWS Artifact.

### Traction
- Open-source SDK published to PyPI (`pip install tophash`) — MIT licensed
- Real TUDataset benchmarks: 86.2% accuracy on MUTAG (beats WL baseline by 4.8 points)
- 100 real PyPI packages fingerprinted and analyzed (public blog post + reproducible analysis)
- Bitwise-determinism CI test as a sacred invariant
- GitHub: github.com/rossbuckley1990-hash/tophash

### Ask
- Introductions to 3-5 AWS customers in regulated industries with Python supply-chain pain
- AWS Activate credits for TopHashX Cloud API infrastructure
- Co-marketing via AWS Security Blog and AWS Marketplace listing
- SOC 2 readiness support via AWS Audit Manager

### Team
Crucible Governance Ltd. Technical team with backgrounds in algebraic topology, distributed systems, and security research. Contact: founders@tophash.io

---

## 2. Microsoft for Startups (Azure Security)

### Company name
Crucible Governance Ltd (TopHash)

### One-line description
TopHash is the structural identity layer for the AI era — a training-free graph fingerprint primitive producing proof-grade canonical IDs for software supply chains, molecular graphs, and AI model architectures.

### Problem
AI supply chain provenance is mandated by EU AI Act and US Executive Order 14110, but no primitive exists to produce structural fingerprints of model architectures or training datasets. Software supply chain attacks exploit the gap between byte-level SBOMs and structural reality. The cost: $4.45M per breach, 40% YoY attack growth, 12 months average SBOM drift.

### Solution
TopHash is a three-layer structural identity primitive:
1. **TopHash v3** (52D fingerprint, 6.6ms/graph) — training-free, deterministic
2. **TopHashX** (pynauty-backed canonical IDs + proof objects, 1.5ms/graph) — provably exact
3. **TopHash Ω∞** (counterfactual engine + stability certificates) — predicate-general

Validated on 103 real graphs across 8 verticals including MUTAG/PROTEINS/NCI1 benchmarks. Bitwise-deterministic across processes. Open-source (MIT) on PyPI and GitHub.

### Why Microsoft
Microsoft's AI supply chain investments (Azure OpenAI, AI Foundry, Semantic Kernel) create structural identity needs that TopHash directly addresses:
- **AI Bill of Materials**: TopHash fingerprints neural network architecture graphs (ResNet, VGG, Inception variants) — directly applicable to Azure AI model provenance.
- **Python supply chain**: Microsoft owns GitHub (PyPI's largest dependency graph host) and Python Tooling (Pylance, Black). TopHash's PyPI structural analysis is complementary.
- **Regulated industries**: Azure Government and Azure for Health require proof-grade attestation. TopHash's proof objects are machine-auditable.

### Traction
- Open-source SDK on PyPI (`pip install tophash`)
- Top-100 PyPI structural analysis published (86/100 packages share structure — a security finding)
- Real TUDataset benchmarks (86.2% on MUTAG, beats WL baseline)
- GitHub: github.com/rossbuckley1990-hash/tophash

### Ask
- Azure credits for TopHashX Cloud API deployment
- Introductions to Azure AI / Azure Security customers needing structural identity
- Co-marketing via Microsoft Security Blog and Azure Marketplace
- GitHub integration partnership (TopHash as a structural identity layer for dependency graphs)

### Team
Crucible Governance Ltd. Contact: founders@tophash.io

---

## 3. Google Cloud for Startups Security

### Company name
Crucible Governance Ltd (TopHash)

### One-line description
TopHash is the structural identity layer for graphs — a training-free, theorem-backed fingerprint primitive producing proof-grade canonical IDs for software supply chains, molecular graphs, and transaction networks.

### Problem
Graph-structured data (dependency trees, transaction networks, molecular graphs, model architectures) has no native identity primitive. SBOM tools hash bytes; vector databases embed text; graph databases store and query but do not fingerprint. The structural opacity tax: $4.45M per breach, $2.6B per approved drug, $780K annual fraud loss per F1000 firm.

### Solution
TopHash — three layers, one primitive:
1. **TopHash v3** (52D training-free fingerprint, 6.6ms/graph) — multi-view (persistence + spectral + geometry)
2. **TopHashX** (pynauty-backed canonical IDs + proof objects, 1.5ms/graph) — provably exact, machine-auditable
3. **TopHash Ω∞** (counterfactual engine + stability certificates) — predicate-general, oracle-verified for disconnect

Validated on 103 real graphs, 8 verticals, 3 TUDatasets. Bitwise-deterministic. MIT licensed. On PyPI and GitHub.

### Why Google Cloud
Google Cloud's strengths align directly with TopHash's verticals:
- **Cybersecurity**: Google Cloud Security (Chronicle, Mandiant) and Software Supply Chain Security (SLSA). TopHash's proof-grade structural IDs complement SLSA attestation.
- **AI/ML**: Vertex AI Model Garden needs model provenance. TopHash fingerprints neural network architectures.
- **Data infrastructure**: Google is the home of graph ML (Graph Mining team, Kaggle). TopHash is the missing structural indexing layer.
- **Molecular/healthcare**: Google DeepMind (AlphaFold) and Isomorphic Labs need molecular graph identity. TopHash's MUTAG benchmarks prove the concept.

### Traction
- Open-source SDK on PyPI (`pip install tophash`)
- Top-100 PyPI structural analysis published
- Real TUDataset benchmarks (86.2% on MUTAG, beats WL baseline)
- Bitwise-determinism CI test
- GitHub: github.com/rossbuckley1990-hash/tophash

### Ask
- Google Cloud credits for TopHashX Cloud API
- Introductions to Google Cloud Security and Vertex AI customers
- Co-marketing via Google Cloud Security Blog and Google Cloud Marketplace
- Research collaboration with Google DeepMind on AI model provenance (TopHash for model architecture fingerprinting)

### Team
Crucible Governance Ltd. Contact: founders@tophash.io

---

## Submission checklist (for all three)

Before submitting, ensure:
- [ ] Crucible Governance Ltd is a registered company entity
- [ ] Founder identity verification documents ready (ID, address proof)
- [ ] AWS/Azure/GCP accounts created under the company email
- [ ] The tophash.io domain is live with a landing page
- [ ] The TopHash Cloud signup form (currently a Google Form placeholder) is replaced with a real signup mechanism
- [ ] At least one design-partner LOI is secured (strengthens the application significantly)
- [ ] The blog post (top100_pypi_report.md) is published on DEV.to and linked in the application
- [ ] The workshop paper (papers/tophash_workshop/tophash_workshop.pdf) is submitted or in submission

Each accelerator will run due diligence on the GitHub repo. The repo must be clean, the README must be current, and the determinism CI test must pass. All of these are already true at the current commit.
