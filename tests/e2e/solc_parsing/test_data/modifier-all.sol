contract C {
    modifier onePlaceholder() {
        _;
    }

    modifier multiplePlaceholders() {
        _;
        _;
        _;
    }

    modifier acceptsVar(uint a) {
        _;
    }

    modifier noParams {
        _;
    }
}