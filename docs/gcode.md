### G-code

    # to exit: ctrl + A, k
    screen /dev/cu.usbmodem21 115200
    
Commands

    ?:
    $I: version/build date
    
Real-Time Commands

    ~: cycle start/resume
    !: feed hold
    ^X: soft-reset
    
GCode

    # G commands act as state machine, you may step in and out of them
    G0 [X<pos>] [Y<pos>] [Z<pos>] - max speed move to position
    G28 - Return to home
    G90 - Absolute mode
    G91 - Incremental mode
    F<int> - move at _feed rate_ F (must be set prior to G1 movements)
    
Status

    <Idle|MPos:0.000,0.000,0.000|FS:0,0|WCO:0.000,0.000,0.000>
    Idle - status
        MPos:0.000,0.000,0.000 - X, Y, Z position
            FS:0,0 - 
               WCO:0.000,0.000,0.000 -