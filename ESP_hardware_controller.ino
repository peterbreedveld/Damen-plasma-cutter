// --- Pinnen Definitie ---
// Encoder 
const int pinEncoderA = 19; 
const int pinEncoderB = 18; 

// Light Gate & Actuatoren
const int pinLightGate = 23;
const int pinMotor = 27;       // Relais voor de loopband
const int pinMotorFast = 26;
const int pinPneumatiek1 = 13; // Ventiel pneumatiek links
const int pinPneumatiek2 = 14; // Ventiel pneumatiek rechts
const int pinPneumatiek3 = 25; //ventiel pneumatiek brug
const int pinPneumatiekSys = 33; // Ventiel voor pneumatische druk 

//Noodstop
const int pinNoodstop = 15;

// --- Volatile Variabelen voor Interrupts ---
volatile long encoderPositie = 0;
volatile long lightGateTriggerPositie = 0;
volatile bool lightGateGetriggerd = false;
volatile bool NoodstopTriggerd = false;
volatile unsigned long noodstopTriggerTijd = 0;
volatile bool lightGateIgnore = false;
// NIEUW: Timer voor de light gate debounce
volatile unsigned long laatsteGateTijd = 0;
//Noodstopdigi
bool digNoodStop = false;

// --- Variabelen voor Motor Sturing ---
bool isMoving = false;
long targetPositie = 0;
long stopPositie = 0;
unsigned long stopTijd = 0;
bool checkOvershoot = false;

//val doorsturen
volatile long oldval = 0;

// --- Interrupt Service Routines (ISR) ---
// Telt de encoder pulsen razendsnel op hardware-niveau
void IRAM_ATTR leesEncoder() {
//  encoderPositie++; <-oude funcite
if (digitalRead(pinEncoderA) == digitalRead(pinEncoderB)) {
    encoderPositie++;
  } else {
    encoderPositie--;
  }
}

// Bevriest de actuele tellerstand op het moment dat het profiel wordt gedetecteerd
void IRAM_ATTR lightGateTrigger() {
  unsigned long huidigeTijd = millis();
  
  // Negeer extra triggers als deze binnen 200ms van de eerste vallen
  if (huidigeTijd - laatsteGateTijd > 200) {
    if (!lightGateIgnore){
      digitalWrite(pinMotor, HIGH);
      lightGateTriggerPositie = encoderPositie;
      lightGateGetriggerd = true;
    }    
    // Reset de timer naar het moment van deze geldige detectie
    laatsteGateTijd = huidigeTijd;
  }
}

// ISR: Registreert bliksemsnel de trigger en de tijd zonder direct actie te ondernemen
void IRAM_ATTR NoodstopTrigger() {
  if (!NoodstopTriggerd) {
    NoodstopTriggerd = true;
    noodstopTriggerTijd = millis();
  }
}

// Centrale functie die alle actuatoren veilig uitschakelt
void activeerNoodstop() {
   digitalWrite(pinMotor, HIGH);
  digitalWrite(pinMotorFast, HIGH);
  digitalWrite(pinPneumatiek1, HIGH);
  digitalWrite(pinPneumatiek2, HIGH);
  digitalWrite(pinPneumatiek3, LOW);
  digitalWrite(pinPneumatiekSys, LOW);
  NoodstopTriggerd = false;
  Serial.println("Noodstop_Engaged");
}
//functies
void reset(){
  encoderPositie = 0;
  Serial.println("RESET_DONE");
  Serial.print("ENC:");
  Serial.println(encoderPositie);
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
  pinMode(pinPneumatiek3, OUTPUT);
  pinMode(pinPneumatiekSys, OUTPUT);

  // Zet alles standaard uit
  digitalWrite(pinMotor, HIGH);
  digitalWrite(pinMotorFast, HIGH);
  digitalWrite(pinPneumatiek1, HIGH);
  digitalWrite(pinPneumatiek2, HIGH);
  digitalWrite(pinPneumatiek3, LOW);
  
  digitalWrite(pinPneumatiekSys, LOW);

  // Koppel Hardware Interrupts
  attachInterrupt(digitalPinToInterrupt(pinEncoderA), leesEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(pinLightGate), lightGateTrigger, RISING);
  attachInterrupt(digitalPinToInterrupt(pinNoodstop), NoodstopTrigger, FALLING);
  
  Serial.println("ESP32 Systeem Gestart. Wacht op commando's...");
}

void loop() {
  // 1. Controleer of de light gate is getriggerd
  if (lightGateGetriggerd) {
    Serial.print("GATE_TRIGGER:");
    Serial.println(lightGateTriggerPositie);
    lightGateGetriggerd = false;
    isMoving = false;
  }

  if (NoodstopTriggerd) {
    // Wacht 50 ms om elektrische ruis/EMI te laten uitdempen
    if (millis() - noodstopTriggerTijd > 50) {
      // Controleer of de pin na 50 ms nog steeds LAAG (0) is
      if (digitalRead(pinNoodstop) == 0) {
        activeerNoodstop();
      } else {
        // Valse trigger door ruis: herstel de status
        NoodstopTriggerd = false;
      }
    }
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
    else if (commando == "Pneumatic_Sys_OFF"){
      digitalWrite(pinPneumatiekSys, LOW);
      Serial.println("ACK:Pneumatic_Sys_OFF");
    }
    else if (commando == "Pneumatic_Sys_ON"){
      digitalWrite(pinPneumatiekSys, HIGH);
      Serial.println("ACK:Pneumatic_Sys_ON");
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
    else if (commando == "CLAMP_3_ON") {
      digitalWrite(pinPneumatiek3, HIGH);
      Serial.println("ACK:CLAMP_3_ON");
    } 
    else if (commando == "CLAMP_3_OFF") {
      digitalWrite(pinPneumatiek3, LOW);
      Serial.println("ACK:CLAMP_3_OFF");
    }    
    else if(commando == "SPEED_FAST"){
      digitalWrite(pinMotorFast, LOW);
      Serial.println("ACK:SPEED_FAST");
    }
    else if(commando == "SPEED_SLOW"){
      digitalWrite(pinMotorFast, HIGH);
      Serial.println("ACK:SPEED_SLOW");
    }
    else if(commando == "RESET"){
      reset();

    }
    else if(commando == "encoderVal"){
      Serial.print("ENC:");
      Serial.println(encoderPositie);
    }
    else if(commando == "DigNoodStop"){
      activeerNoodstop();
      Serial.println("ACK:DigNoodStop");
    }
    else if(commando == "GATE_IGNORE_ON"){
      lightGateIgnore = true;
      Serial.println("ACK:GATE_IGNORE_ON");
    }
    else if(commando == "GATE_IGNORE_OFF"){
      lightGateIgnore = false;
      Serial.println("ACK:GATE_IGNORE_OFF");
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
  //Serial.println(encoderPositie);

  /*if (encoderPositie != oldval){
    Serial.println(encoderPositie);
    oldval = encoderPositie;
    }*/
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
    Serial.print("ENC:");
    Serial.println(encoderPositie);
    checkOvershoot = false;
  }
}