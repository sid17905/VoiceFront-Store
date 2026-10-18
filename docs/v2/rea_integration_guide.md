# REA Integration Guide for VoiceFront-Store

## What is REA?

REA (Reverse Engineer Anything) is an MCP-based reverse engineering toolkit that Tony can use to:
- Analyze JavaScript/Electron applications (extract modules, imports, IPC boundaries)
- Inspect websites and web applications
- Analyze network captures (HAR files)
- Decompile and understand code structures
- Extract UI components from live websites

## REA in VoiceFront-Store Workflow

### 1. **Enhanced Web Scraping** (Primary Use Case)
REA can dramatically improve our component extraction by:
- Deep-inspecting live websites to understand their structure
- Extracting JavaScript module relationships
- Analyzing network traffic to understand API patterns
- Decompiling minified/bundled JavaScript

### 2. **Competitor Analysis**
- Analyze competing storefront platforms
- Understand their feature implementations
- Extract design patterns and UI components

### 3. **Component Library Enhancement**
- Automatically extract reusable components from target sites
- Map component hierarchies and dependencies
- Generate provenance with exact code references

## Installation

```bash
# Install REA globally
npm install -g rea-agents

# Setup REA with Tony (if using Claude/OpenCode agents)
npx rea-agents setup

# Verify installation
rea --version
```

## Integration Points

### A. Enhanced Scraping Tool (`tools/scrape_with_rea.py`)

Instead of just Scrapling/Playwright for DOM extraction, use REA to:
1. **Deep JavaScript Analysis**: Understand React/Vue component structures
2. **Network Observation**: Capture API calls and data flows
3. **Module Mapping**: Extract bundled component code

### B. Live Website Analysis Endpoint

Create `services/analysis-service/` that wraps REA:
```python
# POST /v1/analysis/website
{
  "url": "https://competitor-site.com",
  "extract": ["components", "api_patterns", "javascript_modules"]
}
```

### C. Component Intelligence

REA can analyze:
- How interactive components work (dropdowns, modals, carousels)
- State management patterns
- Event handling logic

## Usage Examples

### Example 1: Analyze a Food Delivery Site
```bash
# Extract JavaScript application structure
rea analyze-javascript-application /path/to/extracted/app --json

# Observe website behavior
rea observe-website "https://www.swiggy.com" --capture-screenshots
```

### Example 2: Network Traffic Analysis
```bash
# Capture network activity
rea capture-website-network "https://www.zomato.com" --output capture.har

# Analyze the HAR file
rea analyze-network-capture capture.har --extract-api-patterns
```

### Example 3: Component Extraction
```bash
# Deep component analysis
rea analyze-web-page "https://www.myntra.com" \
  --extract-components \
  --identify-frameworks \
  --map-interactions
```

## Workflow Integration

### Updated Pipeline (with REA)

```
┌─────────────────────────────────────────────────────────┐
│  1. DISCOVERY PHASE                                      │
│  - Use REA to analyze target websites                   │
│  - Extract JavaScript modules & components               │
│  - Capture network patterns & API structures             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. COMPONENT EXTRACTION                                 │
│  - REA decompiles bundled JS to understand logic        │
│  - Scrapling extracts DOM/CSS                            │
│  - tools/decompose_components.py creates library entries │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. INTELLIGENCE LAYER                                   │
│  - REA identifies interaction patterns                   │
│  - Maps component dependencies                           │
│  - Extracts state management approaches                  │
└─────────────────────────────────────────────────────────┘
```

## Tony's Access

Tony (your AI agent) already has REA available through MCP if:
1. REA is installed (`npm install -g rea-agents`)
2. Setup was run (`npx rea-agents setup`)
3. The agent was restarted

Tony can now use REA tools directly:
- `analyze_javascript_application`
- `observe_website`
- `analyze_network_capture`
- `extract_web_components`

## Action Items

1. **Install REA**: `npm install -g rea-agents`
2. **Create Analysis Service**: New FastAPI service wrapping REA
3. **Enhanced Scraper**: Update `tools/scrape_with_rea.py` to use REA
4. **Documentation**: Add REA usage to component extraction workflow

## Benefits

- **Deeper Insights**: Understand not just what components look like, but how they work
- **Better Provenance**: Exact code references and logic explanations
- **Competitive Intelligence**: Analyze how leading platforms implement features
- **Automated Extraction**: Let Tony analyze sites and extract patterns autonomously
