contract StorageLayout {
    uint248 ALPHA;
    bool BETA;
    uint8 GAMMA;
    struct DELTA {
        bool b;
        uint248 a;
    }
    DELTA EPSILON = DELTA(BETA, ALPHA);
    mapping (uint => DELTA) ZETA;
    mapping (address => mapping (uint => DELTA)) ETA;
    uint248[3] THETA;
    bytes8 IOTA;
    enum KAPPA {
        LAMDA,
        MU,
        NU
    }
    KAPPA XI = KAPPA.LAMDA;
}