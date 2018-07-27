
void setup() {

  Serial.begin(115200);
  

}

// TM_WDG_KEY_LOADING KO 0x12 0x34 0x01 0x82 0xFF 0x7B
void loop() {

  
  byte message[] = {0x12, 0x34, 0x06, 0x80, 0xCA, 0xFE, 0xFE, 0xCA, 0xCA, 0xFF, 0x7B};



  Serial.write(message, sizeof(message));
  Serial.flush();
  delay(1000);

  byte message2[] = {0x12, 0x34, 0x01, 0x66, 0xFF, 0x7B};



  Serial.write(message2, sizeof(message2));
  Serial.flush();
  delay(1000);

  byte message3[] = {0x12, 0x34, 0x00, 0x00, 0x7B};



  Serial.write(message3, sizeof(message3));
  Serial.flush();
  delay(1000);

  




  
}
