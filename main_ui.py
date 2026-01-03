import ast
import subprocess
import os
import shutil
import sys
import serial
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTextEdit, QPushButton, QLabel, QProgressBar, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- SERIAL MONITOR ENGINE ---

class SerialReader(QThread):
    """Thread dedicada à leitura da porta USB (Deep Blue Output)."""
    data_received = pyqtSignal(str)

    def __init__(self, port, baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = False

    def run(self):
        try:
            # Tenta abrir a conexão serial
            ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            self.running = True
            while self.running:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        self.data_received.emit(line)
            ser.close()
        except Exception as e:
            self.data_received.emit(f"[ERRO_SERIAL]: {e}")

    def stop(self):
        self.running = False

# --- CORE ENGINE: COMPILER ---

class MiniCompiler:
    def __init__(self, port="COM5"):
        self.port = port
        user_documents = os.path.join(os.path.expanduser("~"), "Documents")
        self.arduino_tools_dir = os.path.join(user_documents, "Wandi Studio", "Engine", "arduino")
        self.sketch_dir = os.path.join(self.arduino_tools_dir, "build_sketch")
        self.ino_path = os.path.join(self.sketch_dir, "build_sketch.ino")
        
        self.possible_cli_paths = [
            "arduino-cli",
            os.path.join(self.arduino_tools_dir, "arduino-cli.exe"),
            os.path.join(os.getcwd(), "arduino-cli.exe"),
        ]
        self.cpp_lines = []

    def _find_cli(self) -> str:
        for path in self.possible_cli_paths:
            if shutil.which(path) or os.path.exists(path):
                return f'"{path}"' 
        return None

    def translate(self, py_code: str) -> str:
        try:
            tree = ast.parse(py_code)
            self.cpp_lines = ["// Gerado via Wandi Engine - DEEP BLUE SYSTEM", ""]
            
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    self.cpp_lines.append(f"void {node.name}() {{")
                    for stmt in node.body:
                        self._parse_statement(stmt)
                    self.cpp_lines.append("}\n")
            
            return "\n".join(self.cpp_lines)
        except Exception as e:
            return f"// ERRO DE SISTEMA: Verifique a IDENTAÇÃO ou Sintaxe.\n// Detalhe: {e}"

    def _parse_statement(self, stmt):
        """Mapeia os comandos respeitando sua lógica original e adicionando Serial."""
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Name):
                name = call.func.id
                args = []
                for a in call.args:
                    if isinstance(a, ast.Constant):
                        args.append(a.value)
                    elif isinstance(a, ast.Name):
                        args.append(a.id)

                # Mapeamento Wiring (Original + Novos)
                if name == "pinMode":
                    mode = str(args[1]).upper()
                    self.cpp_lines.append(f"  pinMode({args[0]}, {mode});")
                elif name == "digitalWrite":
                    val = str(args[1]).upper()
                    status = "HIGH" if val in ["1", "TRUE", "HIGH"] else "LOW"
                    self.cpp_lines.append(f"  digitalWrite({args[0]}, {status});")
                elif name == "delay":
                    self.cpp_lines.append(f"  delay({args[0]});")
                elif name == "serial_begin":
                    self.cpp_lines.append(f"  Serial.begin({args[0]});")
                elif name == "print":
                    # Tradução de print do Python para Serial.println do Arduino
                    content = f'"{args[0]}"' if isinstance(args[0], str) and args[0] not in ["HIGH", "LOW", "INPUT", "OUTPUT"] else args[0]
                    self.cpp_lines.append(f"  Serial.println({content});")

    def upload(self, cpp_code: str):
        cli_bin = self._find_cli()
        if not cli_bin: return "ERRO: CLI não encontrado."
        if not os.path.exists(self.sketch_dir): os.makedirs(self.sketch_dir, exist_ok=True)
            
        with open(self.ino_path, "w") as f:
            f.write(cpp_code)

        command = f'{cli_bin} compile --upload -p {self.port} -b arduino:avr:uno "{self.sketch_dir}"'
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            return process.stdout if process.returncode == 0 else f"ERRO:\n{process.stderr}"
        except Exception as e: return f"FALHA: {e}"

# --- UI ENGINE: DEEP BLUE INTERFACE ---

class ArduinoIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WANDI ENGINE - DEEP BLUE COMPILER")
        self.compiler = MiniCompiler(port="COM5")
        self.serial_thread = None
        self.init_ui()
        self.apply_deep_blue_style()

    def init_ui(self):
        layout = QVBoxLayout()
        self.status_label = QLabel("> SYSTEM_STATUS: ONLINE")
        layout.addWidget(self.status_label)

        self.code_input = QTextEdit()
        initial_code = (
            "def setup():\n"
            "    serial_begin(9600)\n"
            "    pinMode(13, OUTPUT)\n"
            "\n"
            "def loop():\n"
            "    print(\"WANDI ENGINE ONLINE\")\n"
            "    digitalWrite(13, HIGH)\n"
            "    delay(1000)\n"
            "    digitalWrite(13, LOW)\n"
            "    delay(1000)"
        )
        self.code_input.setPlainText(initial_code)
        layout.addWidget(self.code_input)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        self.btn_run = QPushButton("EXECUTE_DEEP_BLUE_SEQUENCE")
        self.btn_run.clicked.connect(self.start_process)
        layout.addWidget(self.btn_run)

        # Sistema de Abas
        self.tabs = QTabWidget()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.tabs.addTab(self.console, "DEEP_BLUE_LOG")

        self.output_monitor = QTextEdit()
        self.output_monitor.setReadOnly(True)
        self.tabs.addTab(self.output_monitor, "OUTPUT") # Nova aba Output

        self.cpp_viewer = QTextEdit()
        self.cpp_viewer.setReadOnly(True)
        self.tabs.addTab(self.cpp_viewer, "WIRING_SOURCE")
        layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def apply_deep_blue_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #000814; }
            QLabel { color: #00B4D8; font-family: 'Consolas'; }
            QTextEdit { background-color: #001220; color: #CAF0F8; border: 1px solid #003566; font-family: 'Consolas'; }
            QTabWidget::pane { border: 1px solid #003566; background: #000814; }
            QTabBar::tab { background: #001D3D; color: #00B4D8; padding: 10px; border: 1px solid #003566; }
            QTabBar::tab:selected { background: #003566; color: white; border-bottom: 2px solid #ADE8F4; }
            QProgressBar::chunk { background-color: #0077B6; }
            QPushButton { background-color: #003566; color: #CAF0F8; border: 1px solid #00B4D8; padding: 12px; font-weight: bold; }
        """)

    def start_process(self):
        source = self.code_input.toPlainText()
        self.btn_run.setEnabled(False)
        self.output_monitor.clear()
        
        # Para o monitor serial antes de gravar para liberar a porta
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop()
            self.serial_thread.wait()

        self.worker = QThread() # Thread simples para upload
        cpp = self.compiler.translate(source)
        self.cpp_viewer.setText(cpp)
        
        res = self.compiler.upload(cpp)
        self.console.append(res)
        
        # Inicia leitura da aba OUTPUT após sucesso
        if "SUCESSO" in res or "Sketch uses" in res:
            self.start_serial_monitor()
        
        self.btn_run.setEnabled(True)

    def start_serial_monitor(self):
        self.serial_thread = SerialReader(port=self.compiler.port)
        self.serial_thread.data_received.connect(self.update_output)
        self.serial_thread.start()

    def update_output(self, text):
        self.output_monitor.append(f"[>>]: {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoIDE()
    window.show()
    sys.exit(app.exec())