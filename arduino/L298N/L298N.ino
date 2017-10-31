#include <Stepper.h>

// steps per revolution, direction A, direction B
Stepper myStepper(200, 8, 9, 10, 11);
byte message[2];
short step_size;

void setup () {
  myStepper.setSpeed(200);
  Serial.begin(9600);
  Serial.println("ready");
}

void loop () {
  if(Serial.available() == 2) {
    Serial.readBytes(message, 2);
    step_size = message[0];
    step_size += message[1] << 8;
    myStepper.step(step_size);
    Serial.write((byte*)&step_size, sizeof(step_size));
  }
}
