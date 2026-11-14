# AGENTS.md - AI Agent Guidelines for TextToSpeech Backend Workspace

**Location:** `/home/pgfeller/Documents/GitHub/TextToSpeech/backend/`  
**Workspace Type:** Monorepo (Python backend, TypeScript frontend)  
**Date:** 2026-11-14

---

## 🚀 Primary Directive: Memory-First Development

When executing any task in this TextToSpeech **backend** workspace, **you MUST consult the memory system FIRST** before making code changes. This directive applies to all AI agents, including this one.

### Why Consult Memory Before Executing?

The memory system (`/memories/repo/`) contains critical context about:

1. **Workspace Structure**: Monorepo with backend/ (Python), frontend/ (TypeScript/Vite), and service/ (macOS plist)
2. **Technology Stack**: FastAPI/Pydantic (backend), Pytest testing, Python 3.10-3.13 standards
3. **Architecture Patterns**: Clean code, SOLID principles, modular separation of concerns
4. **Feature Capabilities**: 9 modules including backend-prerequisite-management, backend-synthesis, speech-generation
5. **Configuration Files**: `living-specs.yml`, `compose.yaml`, `THIRD_PARTY_NOTICES.md`

### The Memory Consultation Workflow

```mermaid
graphTB
    A[Task Received by AI Agent] --> B{Consult Memory First}
    B --> C{Review workspace-structure.md}
    B --> D{Review tech-stack.md}
    B --> E{Review project-licensing.spec.md}
    
    C --> F{Understand Monorepo Structure}
    D --> F{FastAPI/Pydantic Patterns}
    E --> F{Preserve Licenses & Notices}
    
    F --> G{Understand Backend Architecture Before Coding}
    G --> H[Execute Task]
```

---

## 📋 Mandatory Memory Consultation Steps

**Before ANY task execution**, your AI agent must:

### Step 1: Verify Repository Structure

- Read `/memories/repo/workspace-structure.md`
- Confirm the three-root-directory layout (backend/, frontend/, service/)
- Understand backend/testing structure in `backend/` and `tests/` directories

### Step 2: Review Technology Stack

- Read `/memories/repo/tech-stack.md`
- Verify Python version constraints (3.10-3.13) for backend development
- Confirm FastAPI + Pydantic patterns for API development
- Understand testing framework requirements (pytest)

### Step 3: Check Feature Capabilities

- Review `/capabilities/backend-prerequisite-management/spec.md`
- Review `/capabilities/backend-synthesis/spec.md`
- Review `/capabilities/speech-generation/spec.md`
- Cross-reference with `specs/README.md` living specifications

### Step 4: Preserve Licenses & Security

- Read `THIRD_PARTY_NOTICES.md` before adding new dependencies
- Ensure LICENSE and NOTICE files remain unchanged
- Validate against project licensing requirements in `/project-licensing.spec.md`

---

## 🎯 Memory-Based Decision Making

When faced with decisions, consult memory for guidance:

### Scenario 1: Adding New Backend Feature

**Memory Consultation:**

```python
# Check workspace structure first
memory = "/memories/repo/"
structure = memory + "/workspace-structure.md"

if "backend" in task.lower():
    # Review tech-stack.md for FastAPI/Pydantic patterns
    pattern_file = memory + "/tech-stack.md"
```

**Decision Outcome:** Use `app/routers.py` for new routes, maintain `SpeechService` from `app/services.py`, ensure config uses Pydantic validation from `app/config.py`

### Scenario 2: Creating New API Endpoint

**Memory Consultation:**

```bash
# Review FastAPI routing patterns
cat /memories/repo/tech-stack.md | grep -i "fastapi\|pydantic"
# Check for dependency on SpeechService
grep -n "SpeechService" /memories/repo/workspace-structure.md
```

**Decision Outcome:** Create endpoint in `routers.py`, inject `SpeechService` from `services.py`, use FastAPI `Request` middleware, validate with Pydantic schemas

### Scenario 3: Implementing Test Coverage

**Memory Consultation:**

```bash
# Review existing test structure
cat /memories/repo/workspace-structure.md | grep -A10 "tests"
# Understand pytest conventions
cat /memories/repo/tech-stack.md | grep -i "pytest"
```

**Decision Outcome:** Create tests in `/tests/` directory, use pytest fixtures from `conftest.py`, follow FastAPI testing patterns from tech-stack.md

### Scenario 4: Working with Configuration

**Memory Consultation:**

```bash
# Review configuration layer guidance
cat /memories/repo/tech-stack.md | grep -A10 "config\|settings"
# Check for auth requirements in config.py
grep -n "auth_enabled\|api_key" /memories/repo/workspace-structure.md
```

**Decision Outcome:** Use Pydantic `BaseModel` from `app/config.py`, respect frozen=True constraints, maintain auth requirements in `_SettingsValues` class

---

## 🚫 Forbidden Actions Without Memory Consultation

**Do NOT execute code changes without memory consultation:**

- ❌ Creating new API endpoints without reviewing FastAPI/Pydantic patterns
- ❌ Modifying configuration without understanding Frozen settings behavior
- ❌ Adding dependencies without checking THIRD_PARTY_NOTICES.md
- ❌ Implementing features without cross-referencing capability modules
- ❌ Breaking existing architecture patterns (e.g., replacing Pydantic with non-type-safe alternatives)

---

## 🔍 Memory File Locations Quick Reference

| File | Purpose | When to Consult |
| ------ | --------- | ----------------- |
| `/memories/repo/workspace-structure.md` | Monorepo layout, folder hierarchy | Before understanding architecture |
| `/memories/repo/tech-stack.md` | Tech stack, frameworks, tools | Before coding or deployment |
| `/capabilities/backend-prerequisite-management/spec.md` | Backend prerequisite handling | Before managing backend prerequisites |
| `/capabilities/backend-synthesis/spec.md` | Backend synthesis patterns | Before implementing TTS synthesis |
| `THIRD_PARTY_NOTICES.md` | Dependency audit trail | Before adding new dependencies |

---

## 📌 Memory-First Task Execution Template

**Task received by AI agent:** `{...task_description...}`

**Step 1: Memory Consultation**

```python
# Backend specific memory consultation
memory = "/memories/repo/"

if "backend" in task.lower() or "fastapi" in task.lower():
    # Review tech-stack.md for FastAPI/Pydantic patterns
    structure = memory + "/workspace-structure.md"
    tech_info = memory + "/tech-stack.md"
    
    # Key backend decisions from memory:
    # - Use Pydantic for data validation
    # - Follow FastAPI REST API conventions
    # - Maintain SpeechService separation of concerns
```

**Step 2: Memory-Based Decision**
Based on reviewed files, decide the implementation approach before coding. Document decision in a comment block at top of file.

**Step 3: Execute with Memory Context**
Apply learned patterns from memory while implementing the solution. Use FastAPI/Pydantic patterns consistently.

---

## ⚠️ Important Warnings

### Warning 1: Don't Skip Memory Consultation

Skipping memory consultation can lead to:

- ❌ Breaking existing monorepo structure
- ❌ Using wrong tech stack (e.g., mixing Python in frontend)
- ❌ Violating licensing requirements
- ❌ Missing feature capability boundaries
- ❌ Ignoring Pydantic validation requirements

### Warning 2: Memory Evolves With Project

The memory system is maintained by human developers:

- Review `/memories/repo/` before major refactors
- Check for updated technology constraints (Python 3.10-3.13)
- Monitor capability module changes over time

---

## ✅ Success Criteria

**An AI agent demonstrates successful memory-first development when:**

| Criterion | Memory-Based Behavior | Code Manifestation |
| ----------- | ---------------------- | ------------------- |
| Architecture Awareness | References `workspace-structure.md` | Correct monorepo path usage |
| Tech Stack Alignment | Reviews `tech-stack.md` | FastAPI patterns + Pydantic validation |
| Feature Boundaries | Checks `capabilities/*/spec.md` | Respects feature module boundaries |
| Security/License | Reads `THIRD_PARTY_NOTICES.md` | Proper dependency auditing |

---

## 🔄 Memory System Updates

**AI agents should NOT manually modify memory files.** Memory is maintained by human developers through the `memory` tool with these commands:

- `view`: Read existing memory entries
- `create`: Add new persistent notes (survive across conversations)
- `str_replace`: Modify existing entries in place  
- `delete`: Remove temporary session notes

**Example AI agent memory update request (from human):**

```python
# AI should respond to this query with retrieved content
def consult_memory(query):
    if "backend" in query.lower():
        structure = "/memories/repo/workspace-structure.md"
        tech_info = "/memories/repo/tech-stack.md"
        return f"Backend workspace structure:\n{read_file(structure)}"
```

---

## 📚 Technical References

### Workspace Root

`/home/pgfeller/Documents/GitHub/TextToSpeech/`

### Memory System Base Path

`/memories/repo/` (repository-scoped facts)

### Backend File Structure Quick Access

```bash
tree -L2 backend/
# Output:
backend/
├── app/
│   ├── __init__.py
│   ├── config.py       # FastAPI settings with Pydantic validation
│   ├── language.py      # Language handling logic
│   ├── main.py          # Application factory, RequestBoundaryMiddleware
│   ├── models.py        # Data models using Pydantic
│   ├── routers.py       # API route handlers and decorators
│   ├── services.py      # TTS synthesis orchestration (SpeechService)
│   └── voices.py        # Voice profile management
├── service/             # TTS engine integration (macOS plist)
└── tests/               # Pytest test suites

### Key FastAPI Patterns from Memory
- Application factory pattern in `main.py`
- Dependency injection through `SpeechService`
- Pydantic validation for all data models
- REST API conventions with proper status codes
- Async/await for I/O bound operations

---

**Last Updated:** 2026-11-14  
**Maintained By:** Human developers using the `memory` tool  
**Version:** 1.0  
**Applicable To:** Backend/FastAPI/Python development only
