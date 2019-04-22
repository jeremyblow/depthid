### Load Grbl onto Arduino

1. Launch [Arduino IDE](https://www.arduino.cc/en/Main/Software?).
2. Click `Sketch` from main drop-down menu, select `Include Library` -> `Add .ZIP library`.
3. Navigate to the `depthid/arduino/Grbl/grbl-1.1f.20170801` folder inside this project, 
    highlight the `grbl` folder, and click `Choose`.
4. Click `File` from the main drop-down menu, select `Examples` -> `Grbl` -> `GrblUpload`.
5. Ensure the correct controller (`Tools` -> `Board`) and port (`Tools` -> `Port`) are 
    selected in the main drop-down menu.
6. A new window will appear, click `Upload` within this window.

### Microstep jumpers

[]() | []() | []() | []()
--- | --- | --- | ---
Resolution | M0 | M1 | M2
Full | Low | Low | Low
1/2 | High | Low | Low
1/4 | Low | High | Low
1/8 | High | High | Low
1/16 (A4988) | High | High | High
1/16 (DRV8825) | Low | Low | High
1/32 (DRV8825) | High | Low | High
1/32 (DRV8825) | Low | High | High
1/32 (DRV8825) | High | High | High


### Current

Trim potentiometer CW to limit, trim CCW until step movement ceases, trim CW until movement
is reliable. 