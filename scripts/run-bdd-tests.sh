#!/bin/bash
# BDD Test Runner for Decibel SDK
#
# This script runs the BDD tests for all language SDKs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Decibel SDK BDD Test Runner${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
    echo ""
}

# Function to run tests for a specific SDK
run_sdk_tests() {
    local sdk=$1
    local sdk_dir="$REPO_ROOT/sdk-$sdk"

    print_section "Running BDD tests for $sdk SDK"

    if [ ! -d "$sdk_dir" ]; then
        echo -e "${RED}Error: $sdk SDK directory not found at $sdk_dir${NC}"
        return 1
    fi

    cd "$sdk_dir"

    case $sdk in
        rust)
            if [ -f "Cargo.toml" ]; then
                echo -e "${YELLOW}Running Rust BDD tests...${NC}"
                cargo test --test bdd_basic_test -- --nocapture
                echo -e "${GREEN}✓ Rust BDD tests completed${NC}"
            else
                echo -e "${YELLOW}No Rust tests configured yet${NC}"
            fi
            ;;
        go)
            if [ -f "testbdd/godog_test.go" ]; then
                echo -e "${YELLOW}Running Go BDD tests...${NC}"
                go test -v ./testbdd
                echo -e "${GREEN}✓ Go BDD tests completed${NC}"
            else
                echo -e "${YELLOW}Go BDD tests not yet implemented${NC}"
            fi
            ;;
        kotlin)
            if [ -f "build.gradle.kts" ]; then
                echo -e "${YELLOW}Running Kotlin BDD tests...${NC}"
                gradle test --tests "*Cucumber*"
                echo -e "${GREEN}✓ Kotlin BDD tests completed${NC}"
            else
                echo -e "${YELLOW}Kotlin BDD tests not yet implemented${NC}"
            fi
            ;;
        swift)
            if [ -f "Package.swift" ]; then
                echo -e "${YELLOW}Running Swift BDD tests...${NC}"
                swift test
                echo -e "${GREEN}✓ Swift BDD tests completed${NC}"
            else
                echo -e "${YELLOW}Swift BDD tests not yet implemented${NC}"
            fi
            ;;
        *)
            echo -e "${RED}Unknown SDK: $sdk${NC}"
            return 1
            ;;
    esac
}

# Main execution
main() {
    # Load environment variables from .env file if it exists
    if [ -f "$REPO_ROOT/.env" ]; then
        echo -e "${YELLOW}Loading environment variables from .env${NC}"
        export $(cat "$REPO_ROOT/.env" | grep -v '^#' | xargs)
    fi

    # Check if specific SDK was requested
    if [ $# -gt 0 ]; then
        for sdk in "$@"; do
            run_sdk_tests "$sdk"
        done
    else
        # Run all SDKs
        run_sdk_tests "rust"
        run_sdk_tests "go"
        run_sdk_tests "kotlin"
        run_sdk_tests "swift"
    fi

    print_section "Summary"
    echo -e "${GREEN}All requested BDD test runs completed!${NC}"
    echo ""
    echo "To run tests for a specific SDK:"
    echo "  $ ./scripts/run-bdd-tests.sh rust"
    echo "  $ ./scripts/run-bdd-tests.sh go kotlin"
    echo ""
}

# Run main function
main "$@"
