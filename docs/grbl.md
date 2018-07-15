### Grbl

Grbl is using ENABLE to put the motors in sleep mode when they are not moving - thus reducing power 
consumption and cooling down the drivers.

Getting current adjusted:

 1. find vref adjustment point of driver
 2. use formula to to calc max current per coil for vref
 3. Adjust potentiometer value accordingly