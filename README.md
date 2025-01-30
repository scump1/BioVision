# BioVision Software

A dedicated software using ImageAnalysis for applied science in process engineering and cultivation technology.

## Version Log

### Version 0.5.2:

    - Reworking the measurement handler & worker system based on algorithm (none, bubble, pellet, mixing time...)

### Version 0.5.1.9.5:

    - Added Syringe Pump Support 
    - Integrating Pellet Sizer
    - integrating Pellet Sizing Single Image Analyis Form
    - Reworking Measurement Handling Structure

### Version 0.5.1.9 BETA:

    - Upgraded device state machines complete 
    - Reworked algorithm manager
    - Upgraded Live View performance via background threading
        - Added record option
        - 60 FPS now

### Version 0.5.1.8:

    - Major upgrade to the device state machine
    - Reworking the measurement data structure 

### Version 0.5.1.7:

    - Introduced single image analysis form for a calibration-target image pair with visual feedback for testing
    - Major improvements to the arduino statemachine
    - Major improvements to the algorithm manager statemachine
    - Reworked all base statemachines for devices making them more robust and stable

### Version 0.5.1.6:

    - Bugfixes in Database Form

### Version 0.5.1.5:

    - Implemented an upgrade of the measurement framework
    - full cycle measurement GUI and progressbar 
    - enhanced runtime logic

### Version 0.5.1.4:

    - Upgrade to the event bus 
        -> Now able to execute different tasks in GUI Threads and normal Threads executed by a ThreadPool
        -> More resilient arguments and kwarguments passing
        -> Can now do up to 10 events at the same time independently

### Version 0.5.1.3:

    - Minor bugfixes