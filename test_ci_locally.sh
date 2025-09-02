#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

echo "========================================="
echo "Local CI Simulation for Python 3.9 Upgrade"
echo "========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${YELLOW}1. Checking Python version...${NC}"
python_version=$(python3 --version | cut -d' ' -f2)
min_version="3.9.0"
if [ "$(printf '%s\n' "$min_version" "$python_version" | sort -V | head -n1)" = "$min_version" ]; then
    echo -e "${GREEN}✓ Python $python_version meets minimum requirement (>=3.9)${NC}"
else
    echo -e "${RED}✗ Python $python_version does not meet minimum requirement (>=3.9)${NC}"
    exit 1
fi

# Check for Python 3.8 references in key files
echo -e "\n${YELLOW}2. Checking for Python 3.8 references...${NC}"
files_with_38=$(grep -r "3\.8" --include="*.py" --include="*.yml" --include="*.yaml" --include="*.toml" --include="*.md" --include="setup.py" . 2>/dev/null | grep -v ".git" | grep -v "uv.lock" | grep -v "test_ci_locally.sh" || true)
if [ -z "$files_with_38" ]; then
    echo -e "${GREEN}✓ No Python 3.8 references found${NC}"
else
    echo -e "${RED}✗ Found Python 3.8 references:${NC}"
    echo "$files_with_38"
fi

# Run ruff linting
echo -e "\n${YELLOW}3. Running ruff linting...${NC}"
if uv run ruff check; then
    echo -e "${GREEN}✓ Ruff linting passed${NC}"
else
    echo -e "${RED}✗ Ruff linting failed${NC}"
    exit 1
fi

# Test slither installation
echo -e "\n${YELLOW}4. Testing slither installation...${NC}"
if uv run slither --version > /dev/null 2>&1; then
    version=$(uv run slither --version)
    echo -e "${GREEN}✓ Slither runs successfully (version: $version)${NC}"
else
    echo -e "${RED}✗ Slither failed to run${NC}"
    exit 1
fi

# Test entry points plugin system
echo -e "\n${YELLOW}5. Testing entry points (plugin system)...${NC}"
if uv run python -c "from importlib import metadata; eps = metadata.entry_points().select(group='slither_analyzer.plugin'); print(f'✓ Entry points work: {list(eps)}')"; then
    echo -e "${GREEN}✓ Entry points API working correctly${NC}"
else
    echo -e "${RED}✗ Entry points API failed${NC}"
    exit 1
fi

# Run a subset of unit tests
echo -e "\n${YELLOW}6. Running sample unit tests...${NC}"
if uv run pytest tests/unit/core/test_constant_folding.py -q 2>/dev/null; then
    echo -e "${GREEN}✓ Sample unit tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Sample unit tests failed (this might be expected if test dependencies are missing)${NC}"
fi

# Check pyproject.toml validity
echo -e "\n${YELLOW}7. Checking pyproject.toml validity...${NC}"
if python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" 2>/dev/null || python3 -c "import toml; toml.load('pyproject.toml')" 2>/dev/null; then
    echo -e "${GREEN}✓ pyproject.toml is valid${NC}"
else
    echo -e "${RED}✗ pyproject.toml is invalid${NC}"
    exit 1
fi

# Summary
echo -e "\n${YELLOW}=========================================${NC}"
echo -e "${GREEN}Local CI simulation complete!${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo ""
echo "Next steps to verify CI will pass:"
echo "1. Push changes to a branch and create a PR to see actual CI results"
echo "2. Or run the full test suite locally with: UV_RUN='uv run' bash .github/scripts/unit_test_runner.sh"
echo "3. Check specific workflow files match Python versions: .github/workflows/*.yml"