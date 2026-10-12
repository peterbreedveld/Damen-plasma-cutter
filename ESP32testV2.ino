// --- Pinnen Definitie ---
// Encoder (3.3V logica via spanningsdeler!)
const int pinEncoderA = 19; 
const int pinEncoderB = 18; 

// Light Gate & Actuatoren
const int pinLightGate = 23;
const int pinMotor = 27;       // Relais voor de loopband
const int pinMotorFast = 26;
const int pinPneumatiek1 = 13; // Ventiel pneumatiek links
const int pinPneumatiek2 = 14; // Ventiel pneumatiek rechts

//Noodstop
const int pinNoodstop = 15;

// --- Volatile Variabelen voor Interrupts ---
volatile long encoderPositie = 0;
volatile long lightGateTriggerPositie = 0;
volatile bool lightGateGetriggerd = false;
volatile bool NoodstopTriggerd = false;

// --- Variabelen voor Motor Sturing ---
bool isMoving = false;
long targetPositie = 0;
long stopPositie = 0;
unsigned long stopTijd = 0;
bool checkOvershoot = false;

// --- Interrupt Service Routines (ISR) ---
// Telt de encoder pulsen razendsnel op hardware-niveau
void IRAM_ATTR leesEncoder() {
  encoderPositie++;
/*  if (digitalRead(pinEncoderA) == digitalRead(pinEncoderB)) {
    encoderPositie++;
  } else {
    encoderPositie--;
  }*/
}

// Bevriest de actuele tellerstand op het moment dat het profiel wordt gedetecteerd
void IRAM_ATTR lightGateTrigger() {
  lightGateTriggerPositie = encoderPositie;
  lightGateGetriggerd = true;
}

//noodstop
void IRAM_ATTR NoodstopTrigger() {
  if (digitalRead(pinNoodstop)){
    NoodstopTriggerd = true;
    Serial.print("Noodstop_Engaged");
    }
    else{
      NoodstopTriggerd = false;
      Serial.print("Noodstop_Disengaged");
    }
}

void setup() {
  Serial.begin(115200); // Zorg dat het Python script ook op 115200 baud staat
   
  // Pin configuraties
  pinMode(pinEncoderA, INPUT);
  pinMode(pinEncoderB, INPUT);
  pinMode(pinLightGate, INPUT_PULLUP); // Pas aan indien je sensor actief HOOG is
  pinMode(pinNoodstop, INPUT_PULLDOWN); //zorg er voor dat noodstop normaly closed is en verbonden met 3.3V 
  
  pinMode(pinMotor, OUTPUT);
  pinMode(pinMotorFast, OUTPUT);
  pinMode(pinPneumatiek1, OUTPUT);
  pinMode(pinPneumatiek2, OUTPUT);

  // Zet alles standaard uit
  digitalWrite(pinMotor, HIGH);
  digitalWrite(pinMotorFast, HIGH);
  digitalWrite(pinPneumatiek1, HIGH);
  digitalWrite(pinPneumatiek2, HIGH);

  // Koppel Hardware Interrupts
  attachInterrupt(digitalPinToInterrupt(pinEncoderA), leesEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(pinLightGate), lightGateTrigger, FALLING);
  attachInterrupt(digitalPinToInterrupt(pinNoodstop), NoodstopTrigger, CHANGE);
  
  Serial.println("ESP32 Systeem Gestart. Wacht op commando's...");
}

void loop() {
  // 1. Controleer of de light gate is getriggerd
  if (lightGateGetriggerd) {
    Serial.print("GATE_TRIGGER:");
    Serial.println(lightGateTriggerPositie);
    lightGateGetriggerd = false;
  }

  // 2. Controleer op inkomende seriële commando's van de PC
  if (Serial.available() > 0) {
    String commando = Serial.readStringUntil('\n');
    commando.trim(); // Verwijder witregels/enters

    if (commando == "BELT_ON") {
      digitalWrite(pinMotor, LOW);
      Serial.println("ACK:BELT_ON");
    } 
    else if (commando == "BELT_OFF") {
      digitalWrite(pinMotor, HIGH);
      isMoving = false;
      Serial.println("ACK:BELT_OFF");
    } 
    else if (commando == "CLAMP_1_ON") {
      digitalWrite(pinPneumatiek1, LOW);
      Serial.println("ACK:CLAMP_1_ON");
    } 
    else if (commando == "CLAMP_1_OFF") {
      digitalWrite(pinPneumatiek1, HIGH);
      Serial.println("ACK:CLAMP_1_OFF");
    }
    else if (commando == "CLAMP_2_ON") {
      digitalWrite(pinPneumatiek2, LOW);
      Serial.println("ACK:CLAMP_2_ON");
    } 
    else if (commando == "CLAMP_2_OFF") {
      digitalWrite(pinPneumatiek2, HIGH);
      Serial.println("ACK:CLAMP_2_OFF");
    }
    else if(commando == "SPEED_FAST"){
      digitalWrite(pinMotorFast, LOW);
      Serial.println("ACK:SPEED_FAST");
    }
    else if(commando == "SPEED_SLOW"){
      digitalWrite(pinMotorFast, HIGH);
      Serial.println("ÄCK:SPEED_SLOW");
    }
    else if (commando.startsWith("MOVE:")) {
      long stappen = commando.substring(5).toInt();
      targetPositie = encoderPositie + stappen;
      isMoving = true;
      digitalWrite(pinMotor, LOW);
      Serial.print("ACK:MOVE_STARTED_TARGET:");
      Serial.println(targetPositie);
    }
  }

  // 3. Positie-controle tijdens een autonoom "MOVE" commando
  if (isMoving) {
    if (encoderPositie >= targetPositie) {
      digitalWrite(pinMotor, HIGH); // Stop de band direct
      isMoving = false;
      stopPositie = targetPositie;
      stopTijd = millis();
      checkOvershoot = true;
      Serial.println("STATUS:TARGET_REACHED_MOTOR_OFF");
    }
  }

  // 4. Meet overshoot na het stoppen van de motor
  if (checkOvershoot && (millis() - stopTijd > 500)) {
    long overshoot = encoderPositie - stopPositie;
    Serial.print("OVERSHOOT:");
    Serial.println(overshoot);
    Serial.print("ACTUELE_POS:");
    Serial.println(encoderPositie);
    checkOvershoot = false;
  }
}