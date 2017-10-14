byte message[2];
short step_size;

void setup () {
  Serial.begin(9600);
}

void loop () {
  if(Serial.available() == 2) {
    Serial.readBytes(message, 2);
    step_size = message[0];
    step_size += message[1] << 8;
    Serial.write((byte*)&step_size, sizeof(step_size));
  }
}
