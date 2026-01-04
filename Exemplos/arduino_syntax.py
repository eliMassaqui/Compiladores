SYNTAX_MAP = {
    # --- NÚCLEO ARDUINO (Pinos digitais e analógicos) - Prioridade máxima ---
    "pinMode": "pinMode({0}, {1});",
    "digitalWrite": "digitalWrite({0}, {1});",
    "digitalRead": "digitalRead({0})",
    "analogRead": "analogRead({0})",
    "analogWrite": "analogWrite({0}, {1});",

    # --- TEMPO E CONTROLE ---
    "delay": "delay({0});",
    "millis": "millis()",

    # --- COMUNICAÇÃO SERIAL E I2C ---
    "Serial_begin": "Serial.begin({0});",
    "Serial_println": "Serial.println({0});",
    "Wire_begin": "Wire.begin();",

    # --- SERVOS (Braço Robótico Wandi) ---
    # Foco nos motores vistos no braço azul (wandi-robot.jpg)
    "Servo_attach": "{0}.attach({1});",
    "Servo_write": "{0}.write({1});",

    # --- COMPONENTES VISTOS EM AULA ---

    # LCD I2C (Presente na escola-img-22.jpg)
    "LCD_init": "{0}.init();",
    "LCD_backlight": "{0}.backlight();",
    "LCD_setCursor": "{0}.setCursor({1}, {2});",
    "LCD_print": "{0}.print({1});",
    "LCD_clear": "{0}.clear();",

    # TECLADO MATRICIAL / KEYPAD (Presente na escola-img-3.jpg)
    "Keypad_getKey": "{0}.getKey()",

    # SENSOR ULTRASSÔNICO (HC-SR04 - comum em robótica educacional)
    "Ultrasonic_read": "sonar.ping_cm()",

    # MÓDULO RELÉ (Visto na escola-img-4.jpg)
    "Relay_on": "digitalWrite({0}, LOW);",  # Ativa o relé (Lógica invertida comum)
    "Relay_off": "digitalWrite({0}, HIGH);" # Desativa o relé
}

# Constantes para os alunos usarem no Wandi Engine
CONSTANTS = [
    "HIGH", "LOW", "INPUT", "OUTPUT", "INPUT_PULLUP",
    "LCD_ADDR", "SDA", "SCL", "LED_BUILTIN"
]