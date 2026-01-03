import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel
from compiler_engine import MiniCompiler

class ArduinoIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python to Arduino uploader")
        self.compiler = MiniCompiler(port="COM5") # Altere aqui se necessário
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Área de Código Python
        layout.addWidget(QLabel("Código Python (use: pin_mode, digital_write, delay):"))
        self.code_input = QTextEdit()
        self.code_input.setPlainText("def setup():\n    pin_mode(13, 'OUTPUT')\n\ndef loop():\n    digital_write(13, 1)\n    delay(500)\n    digital_write(13, 0)\n    delay(500)")
        layout.addWidget(self.code_input)

        # Botão de Ação
        self.btn_run = QPushButton("Compilar e Gravar no Arduino (COM5)")
        self.btn_run.clicked.connect(self.process_code)
        layout.addWidget(self.btn_run)

        # Log de Saída
        layout.addWidget(QLabel("Console / Código C++ Gerado:"))
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def process_code(self):
        py_source = self.code_input.toPlainText()
        
        # 1. Tradução
        cpp_code = self.compiler.translate(py_source)
        self.console.setText(f"--- C++ GERADO ---\n{cpp_code}\n\n--- STATUS UPLOAD ---\n")
        
        # 2. Upload (Gravação)
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Gravando... aguarde.")
        
        result = self.compiler.upload(cpp_code)
        
        self.console.append(result)
        self.btn_run.setEnabled(True)
        self.btn_run.setText("Compilar e Gravar no Arduino (COM5)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoIDE()
    window.show()
    sys.exit(app.exec())