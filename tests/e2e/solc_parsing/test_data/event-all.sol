contract C {
    event NoParams();
    event Anonymous() anonymous;
    event OneParam(address addr);
    event OneParamIndexed(address indexed addr);
}