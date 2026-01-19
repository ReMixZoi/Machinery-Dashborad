#!/usr/bin/env python3
"""
Node-RED API Server (Enhanced)
ดึงข้อมูลเครื่องจักรจาก node_red_flow.json และสร้าง API endpoint
รองรับการเติมเครื่องที่ขาด (1-13) และแปลง Keys ให้ตรงกับ Dashboard
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import re
from urllib.parse import urlparse

class NodeRedAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/machines':
            self.serve_machines()
        else:
            self.send_error(404, "Not Found")
    
    def serve_machines(self):
        """ดึงข้อมูลเครื่องจักรจาก node_red_flow.json"""
        try:
            # อ่านไฟล์ node_red_flow.json
            flow_file = os.path.join(os.path.dirname(__file__), 'node_red_flow.json')
            
            flow_data = []
            if os.path.exists(flow_file):
                with open(flow_file, 'r', encoding='utf-8') as f:
                    flow_data = json.load(f)
            
            # ดึงข้อมูลเครื่องจักรจาก flow
            machines = self.extract_machines_from_flow(flow_data)
            
            # ส่งข้อมูลกลับ
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'machines': machines,
                'timestamp': self.get_current_time()
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")
    
    def extract_machines_from_flow(self, flow_data):
        """ดึงข้อมูลเครื่องจักรจาก node_red_flow.json"""
        machines_dict = {}
        
        # 1. สร้าง Base Data สำหรับเครื่อง 1-13 ให้ครบ
        # Format ID ที่พบในระบบคือ 1100-xx, 1200-xx, 1300-xx, 1400-xx
        # เนื่องจากเราไม่รู้ prefix แน่นอน เราจะสร้าง map ตาม suffix ไว้ก่อน
        suffix_map = {
            1: "1200-1", 2: "1200-2", 3: "1300-3", 4: "1300-4", 
            5: "1300-5", 6: "1200-6", 7: "1400-7", 8: "1200-8", 
            9: "1200-9", 10: "1300-10", 11: "1400-11", 12: "1100-12", 
            13: "1300-13"
        }

        # สร้าง default object สำหรับทุก suffix 1-13
        for i in range(1, 14):
            full_id = suffix_map.get(i, f"0000-{i}")
            machines_dict[i] = {
                'id': full_id,
                'name': full_id,
                'model': '-', # รอใส่ข้อมูลจริง
                'presentCycle': 0,
                'lastCycle': 0,
                'stdCycle': 0,
                'cavity': 0,
                'totalPcs': 0,
                'status': False
            }

        # 2. ค้นหา function nodes เพื่อดึงข้อมูลจริงมาทับ
        for node in flow_data:
            if node.get('type') == 'function':
                func_code = node.get('func', '')
                
                # ค้นหา machineID regex patterns
                # แบบที่ 1: var machineID = 12;
                machine_id_match = re.search(r'var machineID\s*=\s*(\d+);', func_code)
                # แบบที่ 2: ดึงจากชื่อเครื่อง เช่น "1200-1" -> suffix 1
                machine_name_match = re.search(r'var machineName\s*=\s*"([\d-]+)";', func_code)
                
                # หา Model (ถ้ามี)
                # ตัวอย่าง: msg.payload.model = "Foam..."; 
                model_match = re.search(r'model["\']?\s*[:=]\s*["\']([^"\']+)["\']', func_code)
                if not model_match:
                    # ลองหาแบบ msg.payload = { model: "..." }
                    model_match = re.search(r'["\']model["\']\s*:\s*["\']([^"\']+)["\']', func_code)

                suffix = None
                full_name = None

                if machine_name_match:
                    full_name = machine_name_match.group(1)
                    # ลองตัด suffix จากชื่อ เช่น 1200-1 -> 1
                    parts = full_name.split('-')
                    if len(parts) > 1 and parts[1].isdigit():
                        suffix = int(parts[1])
                elif machine_id_match:
                    # บางที machineID ในโค้ดคือ suffix เลย
                    suffix = int(machine_id_match.group(1))

                # ถ้าเจอ Suffix ที่ Valid (1-13) ให้อัปเดตข้อมูล
                if suffix and suffix in machines_dict:
                    machine = machines_dict[suffix]
                    
                    if full_name: 
                        machine['name'] = full_name
                        machine['id'] = full_name # ใช้ชื่อเต็มเป็น ID ตามระบบเดิม

                    if model_match:
                        machine['model'] = model_match.group(1)
                    
                    # ลองหาค่าอื่นๆ ถ้ามีการกำหนดค่าเริ่มต้นในโค้ด (Static analysis มีข้อจำกัด)
                    # แต่ Dashboard จะแสดง 0 ถ้าไม่มีข้อมูล ซึ่งตรงตามโจทย์ "รอข้อมูล"

        # 3. แปลงเป็น List และเรียงตาม Suffix 1-13
        # เราใช้ dict key 1-13 เตรียมไว้แล้ว ก็ดึงออกมาเรียงได้เลย
        sorted_machines = [machines_dict[i] for i in range(1, 14)]
        
        return sorted_machines
    
    def get_current_time(self):
        """ดึงเวลาปัจจุบัน"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def run_server(port=1880):
    """เริ่มต้น HTTP Server"""
    # ป้องกัน Port ชน (ถ้า Node-RED จริงรันอยู่ เราอาจจะต้องเปลี่ยน Port แต่ User config ไว้ที่ 1880)
    # เราจะลอง bind ดู
    server_address = ('', port)
    try:
        httpd = HTTPServer(server_address, NodeRedAPIHandler)
        print(f'Node-RED API Server running on http://localhost:{port}')
        httpd.serve_forever()
    except OSError as e:
        print(f"Error: Port {port} is busy. Please stop local Node-RED or change port.")

if __name__ == '__main__':
    run_server()
