# AGENTS.md - Unified AI Agent Guidelines for TextToSpeech Monorepo

**Location:** `/home/pgfeller/Documents/GitHub/TextToSpeech/` (Repository Root)  
**Workspace Type:** Monorepo (Python backend, TypeScript/Vite frontend, macOS service)  
**Date:** 2026-11-14  
**Version:** 2.0

---

## 🚀 Primary Directive: Memory-First Development for Monorepo

When executing any task in this **monorepo** TextToSpeech workspace, **you MUST consult the memory system FIRST** before making code changes. This directive applies to all AI agents across ALL layers (backend/frontend/service).

### Why Consult Memory Before Executing?

The memory system (`/memories/repo/`) contains critical context about:

1. **Workspace Structure**: Monorepo with backend/ (Python), frontend/ (TypeScript/Vite), and service/ (macOS plist)
2. **Technology Stack**:
   - Backend: FastAPI/Pydantic, Python 3.10-3.13, Pytest testing
   - Frontend: Vite/TypeScript/Tailwind, Jest + Playwright E2E testing
   - Service: macOS plist configuration
3. **Architecture Patterns**: Clean code, SOLID principles, modular separation of concerns
4. **Feature Capabilities**: 9 modules including backend-prerequisite-management, speech-generation, accessibility-a11y
5. **Configuration Files**: `living-specs.yml`, `compose.yaml`, `THIRD_PARTY_NOTICES.md`

### The Memory Consultation Workflow

```mermaid
graphTB
    A[Task Received by AI Agent] --> B{Consult Memory First}
    
    B --> C{Review workspace-structure.md}
    B --> D{Review tech-stack.md}
    B --> E{Check capability specs in /capabilities/}
    B --> F{Review licensing requirements}
    
    C --> G1{Maintain Monorepo Structure}
    D --> G2{Use Correct Tech Stack Patterns}
    E --> G3{Respect Feature Boundaries}
    F --> G4{Preserve Licenses & Security}
    
    G1 --> G{Synthesize Integrated Decision}
    G2 --> G
    G3 --> G
    G4 --> G
    
    G --> H[Execute Task]
```

---

## 📋 Mandatory Memory Consultation Steps

**Before ANY task execution**, your AI agent MUST:

### Step 1: Verify Repository Structure (Monorepo Context)

- Read `/memories/repo/workspace-structure.md`
- Confirm three-root-directory layout: `backend/` (Python), `frontend/` (TypeScript/Vite), `service/` (macOS plist)
- Understand testing structure across both backend and frontend
- Note: All code changes must respect monorepo conventions

### Step 2: Review Technology Stack & Language Constraints

- Read `/memories/repo/tech-stack.md`
- Verify Python version constraints (3.10-3.13) for **backend** layer only
- Confirm Vite + TypeScript patterns for **frontend** layer only
- Understand Docker Compose orchestration requirements for multi-container deployment

### Step 3: Check Feature Capabilities & Living Specs

- Review `/capabilities/` directory structure (9 modules total)
- Identify relevant module(s) from the 9 capabilities
- Cross-reference with `specs/README.md` for living specification index
- **Critical**: Determine if feature touches backend, frontend, or both layers

### Step 4: Preserve Licenses & Security Requirements

- Read `THIRD_PARTY_NOTICES.md` before adding new dependencies
- Ensure LICENSE and NOTICE files remain unchanged (do NOT modify)
- Validate against project licensing requirements in `/project-licensing.spec.md`

---

## 🎯 Memory-Based Decision Making Across Monorepo Layers

When faced with decisions, consult memory for guidance:

### Scenario 1: Backend Layer Feature Development

**Memory Consultation:**

```python
# Check monorepo structure first
memory = "/memories/repo/"
structure = memory + "/workspace-structure.md"
backend_info = memory + "/tech-stack.md"

if "backend" in task.lower() or "fastapi" in task.lower():
    # Review tech-stack.md for FastAPI/Pydantic patterns from memory
    structure_file = memory + "/workspace-structure.md"
    
    # Key backend decisions from memory:
    # - Use Pydantic for data validation in all models
    # - Follow FastAPI REST API conventions (status codes, async/await)
    # - Maintain SpeechService separation of concerns in services.py
```

**Decision Outcome:**

- Use `backend/app/routers.py` for new routes
- Inject `SpeechService` from `backend/app/services.py`
- Ensure configuration uses Pydantic validation from `backend/app/config.py`
- **Monorepo consideration**: Backend changes must not break frontend TypeScript compilation

### Scenario 2: Frontend Layer Component Development

**Memory Consultation:**

```python
# Verify Vite/TypeScript patterns
memory = "/memories/repo/"
tech_info = memory + "/tech-stack.md"
structure_file = memory + "/workspace-structure.md"

if "frontend" in task.lower() or "typescript" in task.lower():
    # Review tech-stack.md for Vite/TypeScript/Tailwind patterns from memory
    structure_file = memory + "/workspace-structure.md"
    
    # Key frontend decisions from memory:
    # - Use TypeScript modules (confirmed by package.json "type": "module")
    # - Apply Tailwind utility classes, not inline CSS
    # - Maintain semantic HTML in index.html
```

**Decision Outcome:**

- Use `frontend/app.js` as main entry point with TypeScript compilation
- Apply Tailwind utility classes per tech-stack.md guidance
- Maintain semantic HTML structure from workspace-structure.md context

### Scenario 3: Test Coverage Implementation Across Layers

**Memory Consultation:**

```python
# Review existing test structure
memory = "/memories/repo/"
test_structure_file = memory + "/workspace-structure.md"
backend_tests_info = memory + "/tech-stack.md"

if "test" in task.lower():
    # Backend: Pytest in /backend/tests/
    backend_test_path = memory + "/workspace-structure.md" | grep "tests" | A10
    
    # Frontend: Jest + Playwright E2E in /frontend/tests/
    frontend_test_path = memory + "/tech-stack.md" | grep "jest\|playwright" | A11
    
    # Docker tests: Node.js test runner
    docker_test_path = memory + "/workspace-structure.md" | grep "docker.test" | A12
```

**Decision Outcome:**

- Backend tests: Pytest in `backend/tests/` with fixtures from `conftest.py`
- Frontend tests: Jest unit tests + Playwright E2E in `frontend/tests/e2e/`
- **Monorepo consideration**: Tests must not interfere between layers

### Scenario 4: Cross-Layer Integration Changes

**Memory Consultation:**

```python
# Review monorepo architecture implications
memory = "/memories/repo/"
monorepo_info = memory + "/workspace-structure.md"
cross_layer_info = memory + "/tech-stack.md"

if "integration" in task.lower() or "cross-layer" in task.lower():
    # Backend/frontend integration requires careful memory consultation
    
    # Backend/frontend interaction patterns from memory:
    # - Frontend calls backend via REST API (FastAPI routes)
    # - Frontend serves static assets from Vite build outputs
    # - Docker Compose orchestration connects both layers
```

**Decision Outcome:**

- Cross-layer changes MUST review both `workspace-structure.md` and `tech-stack.md` for consistency
- Consider Docker Compose dependencies in compose.yaml changes
- Update BOTH frontend and backend test suites for cross-layer modifications

---

## 🚫 Forbidden Actions Without Memory Consultation (Monorepo Scope)

**Do NOT execute code changes without memory consultation:**

| Layer | Forbidden Action Without Memory | Consequence |
| ------- | ------------------------------- | -------------- |
| **Backend** | Creating endpoints without reviewing routers.py structure | Breaking API contracts, invalid Pydantic schemas |
| **Frontend** | Modifying components without understanding Vite patterns | TypeScript compilation errors, broken hot module replacement |
| **Service** | Changing macOS plist without tech-stack review | Service startup failures on deployment targets |
| **Monorepo** | Making cross-layer changes without both files consulted | Breaking frontend/backend integration, Docker orchestration issues |

**DO NOT:**

- ❌ Break existing monorepo structure in backend/ or frontend/ directories
- ❌ Use wrong tech stack (e.g., Python code in frontend layer)
- ❌ Violate licensing requirements in THIRD_PARTY_NOTICES.md
- ❌ Ignore feature capability boundaries from /capabilities/ directory

---

## 🔍 Memory File Locations Quick Reference (Monorepo Scope)

| File | Purpose | When to Consult | Layer(s) Affected |
| ------ | --------- | ----------------- | ------------------- |
| `/memories/repo/workspace-structure.md` | Monorepo layout, folder hierarchy | Before understanding architecture | **All layers** |
| `/memories/repo/tech-stack.md` | Tech stack, frameworks, tools | Before coding or deployment | **All layers** |
| `/capabilities/backend-prerequisite-management/spec.md` | Backend prerequisite handling | Before backend prerequisite tasks | Backend |
| `/capabilities/backend-synthesis/spec.md` | Backend synthesis patterns | Before TTS synthesis work | Backend |
| `/capabilities/frontend-image-publishing/spec.md` | Frontend publishing workflows | Before frontend deploy tasks | Frontend |
| `/capabilities/project-licensing.spec.md` | Licensing requirements | Before licensing decisions | **All layers** |

---

## 📌 Monorepo-Specific Memory Execution Template

**Task received by AI agent:** `{...task_description...}`

**Step 1: Memory Consultation (All Layers)**

```python
# MONOREPO-MANDATORY MEMORY CONSULTATION
memory = "/memories/repo/"

# Always review architecture first
structure = memory + "/workspace-structure.md"
# Key questions to ask from structure:
# - Which layer(s) does this task affect?
# - What monorepo conventions apply?
# - Are there cross-layer dependencies?

# Then review tech stack for each affected layer
tech_info = memory + "/tech-stack.md"
# Questions from tech-stack.md:
# - Backend: Python version, FastAPI patterns, Pydantic validation
# - Frontend: Vite configuration, TypeScript modules, Tailwind classes

# Check capability boundaries
capabilities_dir = "/capabilities/"
spec_files = [f for f in capabilities_dir if f.endswith(".md")]
```

**Step 2: Memory-Based Decision (Integrated)**
Based on reviewed files, synthesize decision across ALL affected layers. Document decision in comment block at top of file.

**Decision Checklist:**

- ✅ Does this maintain monorepo structure?
- ✅ Are tech stack patterns consistent within each layer?
- ✅ Have capability boundaries been respected?
- ✅ Will cross-layer dependencies be handled correctly?

**Step 3: Execute with Memory Context**
Apply learned patterns from memory while implementing the solution. Apply FastAPI/Pydantic patterns to backend, Vite/TypeScript/Tailwind to frontend.

---

## ⚠️ Critical Warnings (Monorepo Specific)

### Warning 1: Don't Skip Memory Consultation for ANY Layer

Skipping memory consultation can lead to monorepo-wide issues:

- ❌ Breaking cross-layer integration (backend → frontend)
- ❌ Using wrong tech stack in wrong layer (Python in frontend TypeScript)
- ❌ Violating licensing requirements across all layers
- ❌ Ignoring Docker Compose dependencies when deploying multi-container apps

### Warning 2: Memory Evolves With Project Architecture

The memory system is maintained by human developers:

- Review `/memories/repo/` before major monorepo refactors
- Check for updated technology constraints per layer
- Monitor capability module changes (new features may span multiple layers)

### Warning 3: Cross-Layer Dependencies Require Careful Analysis

When modifying code in one layer affects another:

1. Review `workspace-structure.md` to understand dependency graph
2. Review `tech-stack.md` to ensure compatible patterns
3. Update tests in ALL affected layers
4. Consider Docker Compose changes if multi-container deployment affected

---

## ✅ Success Criteria (Monorepo Memory-First Development)

**An AI agent demonstrates successful monorepo memory-first development when:**

| Criterion | Memory-Based Behavior | Code Manifestation | Layer Impact |
| ----------- | ---------------------- | ------------------- | --------------- |
| **Architecture Awareness** | References `workspace-structure.md` | Correct monorepo path usage | **All layers** |
| **Tech Stack Alignment** | Reviews `tech-stack.md` | FastAPI patterns (backend) OR Vite/TS (frontend) | Layer-specific |
| **Feature Boundaries** | Checks `/capabilities/*/spec.md` | Respects feature module boundaries | Cross-layer if needed |
| **Security/License** | Reads `THIRD_PARTY_NOTICES.md` | Proper dependency auditing | **All layers** |
| **Docker Consistency** | Review `compose.yaml` | Correct multi-container orchestration | Deployment layer |

---

## 🔄 Memory System Updates for Monorepo

**AI agents should NOT manually modify memory files.** Memory is maintained by human developers through the `memory` tool with these commands:

- `view`: Read existing memory entries
- `create`: Add new persistent notes (survive across conversations)
- `str_replace`: Modify existing entries in place  
- `delete`: Remove temporary session notes

**Monorepo-Specific Example AI query:**

```python
def monorepo_memory_query(query):
    """Query memory for any layer affected by task"""
    memory = "/memories/repo/"
    
    if "backend" in query.lower():
        structure = memory + "/workspace-structure.md"
        tech_info = memory + "/tech-stack.md"
        return f"Backend workspace structure:\n{read_file(structure)}\n\nBackend tech stack:\n{read_file(tech_info)}"
    
    elif "frontend" in query.lower():
        structure = memory + "/workspace-structure.md"
        return f"Frontend monorepo context:\n{read_file(structure)}\n\nTech stack for frontend:\n{read_file(memory + '/tech-stack.md')}"
```

---

## 📚 Technical References (Monorepo)

### Workspace Root

`/home/pgfeller/Documents/GitHub/TextToSpeech/`

### Memory System Base Path

`/memories/repo/` (repository-scoped facts, monorepo-wide knowledge)

### Monorepo File Structure Quick Access

```bash
tree -L1 /home/pgfeller/Documents/GitHub/TextToSpeech/
# Output: backend/ frontend/ service/ tests/ docker/ capabilities/ specs/

tree -L2 /home/pgfeller/Documents/GitHub/TextToSpeech/backend/
# Output:
backend/
├── app/                # FastAPI application structure
│   ├── main.py        # Application factory, RequestBoundaryMiddleware
│   ├── config.py      # Settings with Pydantic validation
│   └── routers.py      # API routes and dependency injection
├── service/            # macOS plist configuration for TTS engine
└── tests/             # Pytest test suites

tree -L2 /home/pgfeller/Documents/GitHub/TextToSpeech/frontend/
# Output:
frontend/
├── app.js             # TypeScript main entry point
├── index.html         # Semantic HTML template
├── package.json       # Vite bundler + TypeScript dependencies
└── tests/             # Jest unit tests + Playwright E2E

Key Architecture Patterns from Memory:
| Layer | Primary Pattern | Language Constraints |
|-------|-----------------|---------------------|
| backend | FastAPI REST + Pydantic | Python 3.10-3.13 |
| frontend | Vite modules + Tailwind | TypeScript only |
| service | macOS plist config | Objective-C/Swift |

---

**Last Updated:** 2026-11-14  
**Maintained By:** Human developers using the `memory` tool  
**Version:** 2.0 (Monorepo-Specific)  
**Scope:** All layers (backend/frontend/service)
