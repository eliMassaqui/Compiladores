def setup():
    serial_begin(9600)
    pinMode(13, OUTPUT)

def loop():
    print("WANDI ENGINE ONLINE")
    digitalWrite(13, HIGH)
    delay(1000)
    digitalWrite(13, LOW)
    delay(1000)