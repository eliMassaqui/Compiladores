# Arduino Syntax Reference (Cheat Sheet)

**Estrutura Básica**
```
void setup() {
  // executa 1 vez
}

void loop() {
  // executa repetidamente
}
```

**Tipos de Dados**
```
int, long, float, double
char, boolean, String
byte, unsigned int, unsigned long
```

**Constantes Importantes**
```
HIGH, LOW
INPUT, OUTPUT, INPUT_PULLUP
```

**I/O Digital**
```
pinMode(pin, MODE)
digitalWrite(pin, HIGH/LOW)
digitalRead(pin)
```

**I/O Analógico**
```
analogRead(pin)       // 0-1023
analogWrite(pin, val) // PWM 0-255
```

**Funções de Tempo**
```
delay(ms)
delayMicroseconds(us)
millis()   // tempo desde start em ms
micros()   // tempo desde start em μs
```

**Matemática**
```
abs(x), constrain(x,a,b), map(val,fLow,fHigh,tLow,tHigh)
min(a,b), max(a,b)
pow(x,y), sqrt(x), round(x)
sin(x), cos(x), tan(x)
```

**Comunicação Serial**
```
Serial.begin(9600)
Serial.print("texto")
Serial.println("texto")
Serial.read()
Serial.available()
```

**Controle de Fluxo**
```
if(cond) { ... } else { ... }
for(i=0;i<N;i++) { ... }
while(cond) { ... }
do { ... } while(cond)
switch(var) { case x: ...; break; ... }
```

**Funções Avançadas**
```
tone(pin,freq), noTone(pin)
bitRead(val,bit), bitWrite(val,bit,bv)
bitSet(val,bit), bitClear(val,bit)
randomSeed(seed), random(max), random(min,max)
```

**Estruturas de Dados**
```
int arr[5] = {1,2,3,4,5}
String s = "hello"
s.length(), s.substring(0,3), s.indexOf("e")
struct Point { int x; int y; };
Point p1 = {10,20};
```

**Exemplo Completo**
```
int led = 13;

void setup() {
  pinMode(led, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  digitalWrite(led, HIGH);
  Serial.println("LED ON");
  delay(1000);
  digitalWrite(led, LOW);
  Serial.println("LED OFF");
  delay(1000);
}
```

