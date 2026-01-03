import ast
import subprocess
import os
import shutil
import sys
import serial
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QLabel, QProgressBar, QTabWidget, QLineEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- SERIAL ENGINE ---

class SerialHandler(QThread):
    """Thread para leitura e escrita na porta USB com feedback de status."""
    data_received = pyqtSignal(str)
    status_signal = pyqtSignal(bool) # Novo sinal para status da conexão

    def __init__(self, port, baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.serial_conn = None

    def run(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
            self.running = True
            self.status_signal.emit(True) # Conectado com sucesso
            while self.running:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        self.data_received.emit(line)
            if self.serial_conn:
                self.serial_conn.close()
        except Exception as e:
            self.data_received.emit(f"[ERRO_SERIAL]: {e}")
            self.status_signal.emit(False) # Falha na conexão

    def write(self, data):
        """Envia dados para o Arduino."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(data.encode('utf-8'))

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
            return f"// ERRO DE SISTEMA: Verifique a IDENTAÇÃO.\n// Detalhe: {e}"

    def _parse_statement(self, stmt):
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Name):
                name = call.func.id
                args = [a.value if isinstance(a, ast.Constant) else a.id for a in call.args]

                if name == "pinMode":
                    self.cpp_lines.append(f"  pinMode({args[0]}, {str(args[1]).upper()});")
                elif name == "digitalWrite":
                    status = "HIGH" if str(args[1]).upper() in ["1", "TRUE", "HIGH"] else "LOW"
                    self.cpp_lines.append(f"  digitalWrite({args[0]}, {status});")
                elif name == "delay":
                    self.cpp_lines.append(f"  delay({args[0]});")
                elif name == "serial_begin":
                    self.cpp_lines.append(f"  Serial.begin({args[0]});")
                elif name == "print":
                    content = f'"{args[0]}"' if isinstance(args[0], str) else args[0]
                    self.cpp_lines.append(f"  Serial.println({content});")

    def upload(self, cpp_code: str):
        cli_bin = self._find_cli()
        if not cli_bin: return "ERRO: CLI não encontrado."
        if not os.path.exists(self.sketch_dir): os.makedirs(self.sketch_dir, exist_ok=True)
        with open(self.ino_path, "w") as f: f.write(cpp_code)
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
        self.serial_handler = None
        self.init_ui()
        self.apply_deep_blue_style()

    def init_ui(self):
        layout = QVBoxLayout()
        self.status_label = QLabel("> SYSTEM_STATUS: ONLINE")
        layout.addWidget(self.status_label)

        self.code_input = QTextEdit()
        self.code_input.setPlainText("def setup():\n    serial_begin(9600)\n\ndef loop():\n    delay(100)")
        layout.addWidget(self.code_input)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        self.btn_run = QPushButton("EXECUTE_DEEP_BLUE_SEQUENCE")
        self.btn_run.clicked.connect(self.start_process)
        layout.addWidget(self.btn_run)

        self.tabs = QTabWidget()
        
        # Aba 1: Output (Logs do Sistema)
        self.output_monitor = QTextEdit()
        self.output_monitor.setReadOnly(True)
        self.tabs.addTab(self.output_monitor, "OUTPUT")

        # Aba 2: Serial Monitor (Comunicação Real-time)
        serial_widget = QWidget()
        serial_layout = QVBoxLayout()
        self.serial_console = QTextEdit()
        self.serial_console.setReadOnly(True)
        
        # Container para Input e Botão Connect
        input_container = QHBoxLayout()
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Serial Input - Press Enter to Send")
        self.serial_input.returnPressed.connect(self.send_serial_data)
        
        self.btn_serial_toggle = QPushButton("CONNECT")
        self.btn_serial_toggle.setFixedWidth(120)
        self.btn_serial_toggle.clicked.connect(self.toggle_serial)
        
        input_container.addWidget(self.serial_input)
        input_container.addWidget(self.btn_serial_toggle)
        
        serial_layout.addWidget(self.serial_console)
        serial_layout.addLayout(input_container)
        serial_widget.setLayout(serial_layout)
        self.tabs.addTab(serial_widget, "SERIAL MONITOR")

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
            QTextEdit, QLineEdit { background-color: #001220; color: #CAF0F8; border: 1px solid #003566; font-family: 'Consolas'; padding: 5px; }
            QTabWidget::pane { border: 1px solid #003566; background: #000814; }
            QTabBar::tab { background: #001D3D; color: #00B4D8; padding: 10px; border: 1px solid #003566; }
            QTabBar::tab:selected { background: #003566; color: white; border-bottom: 2px solid #ADE8F4; }
            QPushButton { background-color: #003566; color: #CAF0F8; border: 1px solid #00B4D8; padding: 12px; font-weight: bold; }
        """)

    def toggle_serial(self):
        """Liga ou desliga a conexão serial sem compilar."""
        if self.serial_handler and self.serial_handler.isRunning():
            self.serial_handler.stop()
            self.serial_handler.wait()
            self.update_serial_status_ui(False)
        else:
            self.start_serial_handler()

    def start_process(self):
        """Lógica de Upload (Fecha a serial se estiver aberta para não dar conflito)."""
        source = self.code_input.toPlainText()
        self.btn_run.setEnabled(False)
        self.output_monitor.clear()
        
        # Fecha a porta para o arduino-cli poder usar
        if self.serial_handler and self.serial_handler.isRunning():
            self.serial_handler.stop()
            self.serial_handler.wait()
            self.update_serial_status_ui(False)

        self.output_monitor.append("[SYS]: Analisando Deep Blue AST...")
        cpp = self.compiler.translate(source)
        self.cpp_viewer.setText(cpp)
        
        res = self.compiler.upload(cpp)
        self.output_monitor.append(f"\n[REPORT]:\n{res}")
        
        # Se upload ok, religa a serial automaticamente
        if "SUCESSO" in res or "Sketch uses" in res:
            self.start_serial_handler()
        self.btn_run.setEnabled(True)

    def start_serial_handler(self):
        self.serial_handler = SerialHandler(port=self.compiler.port)
        self.serial_handler.data_received.connect(self.update_serial_console)
        self.serial_handler.status_signal.connect(self.update_serial_status_ui)
        self.serial_handler.start()

    def update_serial_status_ui(self, connected):
        """Atualiza o visual do botão baseado na conexão."""
        if connected:
            self.btn_serial_toggle.setText("DISCONNECT")
            self.btn_serial_toggle.setStyleSheet("background-color: #023E8A; color: white;")
            self.serial_console.append("[SYS]: Connected to Serial Port.")
        else:
            self.btn_serial_toggle.setText("CONNECT")
            self.btn_serial_toggle.setStyleSheet("background-color: #003566; color: #CAF0F8;")
            self.serial_console.append("[SYS]: Disconnected.")

    def send_serial_data(self):
        if self.serial_handler and self.serial_handler.isRunning():
            data = self.serial_input.text()
            if data:
                self.serial_handler.write(data)
                self.serial_console.append(f"[SENT]: {data}")
                self.serial_input.clear()

    def update_serial_console(self, text):
        self.serial_console.append(f"[RECV]: {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoIDE()
    window.show()
    sys.exit(app.exec())