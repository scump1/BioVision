#include <Servo.h>

#include <Wire.h>
#include "WaveShare_MLX90614.h"

WaveShare_MLX90614 IRCamera = WaveShare_MLX90614();

#define Fan1Pin 6
#define Fan2Pin 5


#define ServoPin 3

//Servo
Servo light_servo;

//Variablen Definition
float target_temperature = 32;
float current_temperature;

int fanspeed = 128;
int angle;

void setup() {

  //Servo
  light_servo.attach(ServoPin);
  light_servo.write(0);

  //Serial 
  Serial.begin(115200);

  //Pin Modes
  pinMode(Fan1Pin, OUTPUT);
  pinMode(Fan2Pin, OUTPUT);
  pinMode(4, OUTPUT);

  //Camera
  IRCamera.begin();
}

void loop() {

  pollSerial(); // We look for serial commands
  
  calculateFanSpeed(); // we calculate a fan speed based on the given data
  poll_temp(); // we poll the IR Cam Temp

}

void pollSerial() {

  if (Serial.available() > 0) {
    char command = (char)Serial.read();
    delay(50);

    switch (command) {

      case 'H':
        Serial.println("Y");
        break;

      case 'T':
      
        if (Serial.available() > 0) {
          delay(100);
          target_temperature = Serial.parseFloat();
          Serial.println(target_temperature);
        }
        break;

      case 'R':
        Serial.println(current_temperature);
        Serial.println(target_temperature);
        Serial.println(fanspeed);
        break;

      case 'S':
      
        if (Serial.available() > 0) {
          delay(100);
          angle = Serial.parseFloat();
          Serial.println(angle);
          adjust_servo_state();
        break;
        }
    }
  }
}

// This calculates a fan speed via a plotted function -> under target means higher rpm, at target means base speed, above target is approaching zero speed
void calculateFanSpeed() {
  // Calculate the temperature difference
  float diff = target_temperature - current_temperature;

  // Fan speed control range
  const int min_fan_speed = 10; // Define your minimum speed for the fan
  const int max_fan_speed = 255;            // Maximum fan speed

  // Apply proportional control based on the temperature difference
  if (diff > 0) { // When current temperature is below target
    // Map the difference to a speed range
    //Scaling the diff *10 -> 0.1 difference would be 1
    diff *= 10;
    fanspeed = map(diff, 0, 10, min_fan_speed, max_fan_speed); // Adjust '10' based on how aggressively you want the fan to respond
    fanspeed = constrain(fanspeed, min_fan_speed, max_fan_speed); // Limit within min and max
  } else if (diff <= 0) { // When current temperature reaches or exceeds target
    // Decrease fan speed proportionally as temperature approaches or exceeds target
    //Scaling the diff *10
    diff = abs(diff * 10);
    fanspeed = map(diff, 0, 10, min_fan_speed, 0);
    fanspeed = constrain(fanspeed, 0, max_fan_speed);
  }

  // Update fan speed
  set_fan_speed(fanspeed);
}

void set_fan_speed(int fanspeed) {
  analogWrite(Fan1Pin, fanspeed);
  analogWrite(Fan2Pin, fanspeed);
}

void poll_temp() {
  // Constants for the polling interval and read delay
  const unsigned long pollingInterval = 2000;  // 5 seconds in milliseconds
  const unsigned long readDelay = 100;         // Delay between reads for averaging
  
  // Static variables to accumulate data between polls
  static unsigned long lastPollTime = 0;
  static unsigned long lastReadTime = 0;
  static float tempSum = 0;       // Sum of temperature readings for averaging
  static int readCount = 0;       // Count of readings for averaging
  
  // Current time
  unsigned long currentTime = millis();

  // Take a new reading if at least `readDelay` ms has passed since the last read
  if (currentTime - lastReadTime >= readDelay) {
    lastReadTime = currentTime;
    float newTemp = IRCamera.readObjectTemp();
    if (!isnan(newTemp)) {    // Ensure reading is valid
      tempSum += newTemp;      // Accumulate valid reading
      readCount++;             // Increment count of readings
    }
  }

  // If 5 seconds have passed, calculate the average
  if (currentTime - lastPollTime >= pollingInterval) {
    lastPollTime = currentTime;
    if (readCount > 0) {
      current_temperature = tempSum / readCount;  // Average temperature
    }
    
    // Reset the accumulator and counter for the next interval
    tempSum = 0;
    readCount = 0;
  }
}

void adjust_servo_state() {
  if (angle == 1) {
    light_servo.write(90);
  }
  else if (angle == 0) {
    light_servo.write(0);
  }
}