import ast
import subprocess
import os
import shutil
import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QLabel, QProgressBar, QTabWidget, 
                             QLineEdit, QToolBar, QFileDialog, QComboBox)
from PyQt6.QtGui import QTextCursor, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- SERIAL ENGINE ---

class SerialHandler(QThread):
    data_received = pyqtSignal(str)
    status_signal = pyqtSignal(bool)

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
            self.status_signal.emit(True)
            while self.running:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        self.data_received.emit(line)
            if self.serial_conn:
                self.serial_conn.close()
        except Exception as e:
            self.data_received.emit(f"[ERRO_SERIAL]: {e}")
            self.status_signal.emit(False)

    def write(self, data):
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

    def _find_cli(self) -> str:
        for path in self.possible_cli_paths:
            if shutil.which(path) or os.path.exists(path): return f'"{path}"' 
        return None

# --- UI ENGINE ---

class ArduinoIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WANDI ENGINE - DEEP BLUE COMPILER")
        self.compiler = MiniCompiler()
        self.serial_handler = None
        self.current_file = None
        self.init_ui()
        self.apply_deep_blue_style()
        self.refresh_ports()

    def init_ui(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Ações de Arquivo
        toolbar.addAction(QAction("NEW", self, triggered=self.new_file))
        toolbar.addAction(QAction("OPEN", self, triggered=self.open_file))
        toolbar.addAction(QAction("SAVE", self, triggered=self.save_file))
        toolbar.addSeparator()
        toolbar.addAction(QAction("EXECUTE", self, triggered=self.start_process))
        toolbar.addSeparator()

        # Seletor de Porta
        toolbar.addWidget(QLabel(" PORT: "))
        self.port_combo = QComboBox()
        self.port_combo.setFixedWidth(100)
        self.port_combo.currentTextChanged.connect(self.update_compiler_port)
        toolbar.addWidget(self.port_combo)
        
        refresh_action = QAction("🔄", self)
        refresh_action.triggered.connect(self.refresh_ports)
        toolbar.addAction(refresh_action)

        layout = QVBoxLayout()
        self.status_label = QLabel("> SYSTEM_STATUS: ONLINE")
        layout.addWidget(self.status_label)

        self.code_input = QTextEdit()
        self.code_input.setPlainText("def setup():\n    serial_begin(9600)\n\ndef loop():\n    delay(100)")
        layout.addWidget(self.code_input)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        self.tabs = QTabWidget()
        self.output_monitor = QTextEdit()
        self.output_monitor.setReadOnly(True)
        self.tabs.addTab(self.output_monitor, "OUTPUT")

        # Serial Tab
        serial_widget = QWidget()
        serial_layout = QVBoxLayout()
        self.serial_console = QTextEdit()
        self.serial_console.setReadOnly(True)
        input_container = QHBoxLayout()
        self.serial_input = QLineEdit()
        self.serial_input.returnPressed.connect(self.send_serial_data)
        self.btn_serial_toggle = QPushButton("CONNECT")
        self.btn_serial_toggle.clicked.connect(self.toggle_serial)
        input_container.addWidget(self.serial_input)
        input_container.addWidget(self.btn_serial_toggle)
        serial_layout.addWidget(self.serial_console)
        serial_layout.addLayout(input_container)
        serial_widget.setLayout(serial_layout)
        self.tabs.addTab(serial_widget, "SERIAL MONITOR")

        self.cpp_viewer = QTextEdit()
        self.tabs.addTab(self.cpp_viewer, "WIRING_SOURCE")
        layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def apply_deep_blue_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #000814; }
            QToolBar { background-color: #001D3D; border: 1px solid #003566; padding: 5px; color: #CAF0F8; }
            QComboBox { background-color: #001220; color: #00B4D8; border: 1px solid #003566; padding: 2px; }
            QLabel { color: #00B4D8; font-family: 'Consolas'; }
            QTextEdit, QLineEdit { background-color: #001220; color: #CAF0F8; border: 1px solid #003566; font-family: 'Consolas'; }
            QTabWidget::pane { border: 1px solid #003566; background: #000814; }
            QTabBar::tab { background: #001D3D; color: #00B4D8; padding: 10px; border: 1px solid #003566; }
            QTabBar::tab:selected { background: #003566; color: white; }
            QPushButton { background-color: #003566; color: #CAF0F8; border: 1px solid #00B4D8; padding: 10px; font-weight: bold; }
        """)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)
        if not ports:
            self.status_label.setText("> NO_DEVICE_DETECTED")
        else:
            self.status_label.setText(f"> {len(ports)} PORT(S) FOUND")

    def update_compiler_port(self, port_name):
        self.compiler.port = port_name

    def new_file(self):
        self.code_input.clear()
        self.current_file = None

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Source", "", "Python Files (*.py)")
        if file_path:
            with open(file_path, 'r') as f: self.code_input.setPlainText(f.read())
            self.current_file = file_path

    def save_file(self):
        if not self.current_file:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Source", "", "Python Files (*.py)")
            if file_path: self.current_file = file_path
            else: return
        with open(self.current_file, 'w') as f: f.write(self.code_input.toPlainText())

    def toggle_serial(self):
        if self.serial_handler and self.serial_handler.isRunning():
            self.serial_handler.stop()
            self.serial_handler.wait()
            self.update_serial_status_ui(False)
        else:
            self.start_serial_handler()

    def start_process(self):
        if not self.compiler.port:
            self.output_monitor.append("[ERR]: Nenhuma porta selecionada!")
            return
        
        if self.serial_handler and self.serial_handler.isRunning():
            self.serial_handler.stop()
            self.serial_handler.wait()
            self.update_serial_status_ui(False)

        self.output_monitor.append(f"[SYS]: Iniciando em {self.compiler.port}...")
        cpp = self.compiler.translate(self.code_input.toPlainText())
        self.cpp_viewer.setText(cpp)
        res = self.compiler.upload(cpp)
        self.output_monitor.append(f"\n[REPORT]:\n{res}")
        if "SUCESSO" in res or "Sketch" in res:
            self.start_serial_handler()

    def start_serial_handler(self):
        if self.compiler.port:
            self.serial_handler = SerialHandler(port=self.compiler.port)
            self.serial_handler.data_received.connect(self.update_serial_console)
            self.serial_handler.status_signal.connect(self.update_serial_status_ui)
            self.serial_handler.start()

    def update_serial_status_ui(self, connected):
        if connected:
            self.btn_serial_toggle.setText("DISCONNECT")
            self.serial_console.append(f"[SYS]: Connected to {self.compiler.port}")
        else:
            self.btn_serial_toggle.setText("CONNECT")
            self.serial_console.append("[SYS]: Disconnected.")

    def send_serial_data(self):
        if self.serial_handler and self.serial_handler.isRunning():
            data = self.serial_input.text()
            self.serial_handler.write(data)
            self.serial_console.append(f"[SENT]: {data}")
            self.serial_input.clear()

    def update_serial_console(self, text):
        self.serial_console.append(f"[RECV]: {text}")
        self.serial_console.moveCursor(QTextCursor.MoveOperation.End)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoIDE()
    window.show()
    sys.exit(app.exec())