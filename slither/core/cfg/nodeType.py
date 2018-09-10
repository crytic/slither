class NodeType:

    ENTRYPOINT = 0x0  # no expression

    # Node with expression

    EXPRESSION = 0x10  # normal case
    RETURN = 0x11      # RETURN may contain an expression
    IF = 0x12
    VARIABLE = 0x13    # Declaration of variable
    ASSEMBLY = 0x14
    IFLOOP = 0x15

    # Below the nodes have no expression
    # But are used to expression CFG structure

    # Absorbing node
    THROW = 0x20

    # Loop related nodes
    BREAK = 0x31
    CONTINUE = 0x32

    # Only modifier node
    PLACEHOLDER = 0x40

    # Merging nodes
    # Unclear if they will be necessary
    ENDIF = 0x50
    STARTLOOP = 0x51
    ENDLOOP = 0x52

    @staticmethod
    def str(t):
        if t == 0x0:
            return 'EntryPoint'
        if t == 0x10:
            return 'Expressions'
        if t == 0x11:
            return 'Return'
        if t == 0x12:
            return 'If'
        if t == 0x13:
            return 'New variable'
        if t == 0x14:
            return 'Inline Assembly'
        if t == 0x15:
            return 'IfLoop'
        if t == 0x20:
            return 'Throw'
        if t == 0x31:
            return 'Break'
        if t == 0x32:
            return 'Continue'
        if t == 0x40:
            return '_'
        if t == 0x50:
            return 'EndIf'
        if t == 0x51:
            return 'BeginLoop'
        if t == 0x52:
            return 'EndLoop'
        return 'Unknown type {}'.format(hex(t))
