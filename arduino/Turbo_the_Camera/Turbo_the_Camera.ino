#include <Stepper.h>

// steps per revolution, direction A, direction B
Stepper myStepper(200, 12, 13);
byte message[2];
short step_size;

void setup () {
  // Set pins
  pinMode(3, OUTPUT);       // PWM A
  pinMode(11, OUTPUT);      // PWM B
  pinMode(9, OUTPUT);       // Brake A
  pinMode(8, OUTPUT);       // Brake B
  digitalWrite(3, HIGH);    // PWM A
  digitalWrite(11, HIGH);   // PWM B
  digitalWrite(9, LOW);     // Brake A
  digitalWrite(8, LOW);     // Brake B
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
