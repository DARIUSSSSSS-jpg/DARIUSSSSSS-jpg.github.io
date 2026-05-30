"""
BLENDER CAMERA CONTROLLER v3 - Professional
Controla la cámara 3D en Blender en tiempo real desde el móvil
Soporta: Rotación + Acelerómetro + Duración dinámica de frames

INSTALACIÓN:
1. Blender > Scripting > New
2. Copiar este código
3. Alt + P para ejecutar
"""

import bpy
import json
import math
import threading
import socket
from collections import deque
import time

class ProfessionalCameraController:
    def __init__(self):
        self.is_running = False
        self.server_socket = None
        self.rotation_smoothing = 0.7
        self.position_smoothing = 0.8
        self.last_rotation = [0, 0, 0]
        self.last_position = [0, 0, 0]
        self.port = 5005
        self.rotation_history = deque(maxlen=10)
        self.position_history = deque(maxlen=10)
        self.position_scale = 0.1
        self.camera_base_position = [0, 0, 0]
        self.is_recording = False
        self.current_frame = 0
        self.max_frames = 100
        
        self.stats = {
            'packets_received': 0,
            'last_update': 0,
            'fps': 0,
            'frame_count': 0,
            'last_acceleration': [0, 0, 0]
        }
        
    def get_active_camera(self):
        camera = bpy.context.scene.camera
        if not camera:
            print("No active camera in scene")
            return None
        return camera
    
    def apply_rotation_smoothing(self, new_rotation):
        smoothed = [
            self.last_rotation[i] * self.rotation_smoothing + new_rotation[i] * (1 - self.rotation_smoothing)
            for i in range(3)
        ]
        self.last_rotation = smoothed
        return smoothed
    
    def apply_position_smoothing(self, new_position):
        smoothed = [
            self.last_position[i] * self.position_smoothing + new_position[i] * (1 - self.position_smoothing)
            for i in range(3)
        ]
        self.last_position = smoothed
        return smoothed
    
    def rotate_camera(self, alpha, beta, gamma, gx=0, gy=0, gz=0, is_recording=False, frame=0):
        camera = self.get_active_camera()
        if not camera:
            return
        
        # ROTACIÓN con corrección de ejes invertidos
        x_rad = -math.radians(beta)
        y_rad = -math.radians(gamma)
        z_rad = math.radians(alpha)
        
        smoothed_rotation = self.apply_rotation_smoothing([x_rad, y_rad, z_rad])
        
        camera.rotation_euler[0] = smoothed_rotation[0]
        camera.rotation_euler[1] = smoothed_rotation[1]
        camera.rotation_euler[2] = smoothed_rotation[2]
        
        # POSICIÓN desde acelerómetro
        self.position_history.append([gx, gy, gz])
        
        if len(self.position_history) > 0:
            avg_gx = sum(p[0] for p in self.position_history) / len(self.position_history)
            avg_gy = sum(p[1] for p in self.position_history) / len(self.position_history)
            avg_gz = sum(p[2] for p in self.position_history) / len(self.position_history)
        else:
            avg_gx, avg_gy, avg_gz = 0, 0, 0
        
        smoothed_position = self.apply_position_smoothing([
            avg_gx * self.position_scale,
            avg_gz * self.position_scale,
            avg_gy * self.position_scale
        ])
        
        camera.location[0] = self.camera_base_position[0] + smoothed_position[0]
        camera.location[1] = self.camera_base_position[1] + smoothed_position[1]
        camera.location[2] = self.camera_base_position[2] + smoothed_position[2]
        
        # KEYFRAMES si está grabando
        if is_recording and bpy.context.scene.is_animation_playing:
            try:
                camera.keyframe_insert(data_path="rotation_euler", frame=frame)
                camera.keyframe_insert(data_path="location", frame=frame)
            except:
                pass
        
        self.stats['packets_received'] += 1
        self.stats['frame_count'] += 1
        self.stats['last_update'] = time.time()
        
        if self.stats['frame_count'] % 20 == 0:
            print(f"Frame {frame}/{self.max_frames} | Rot: A={alpha:.0f}° B={beta:.0f}° G={gamma:.0f}° | Acc: {gx:.2f}, {gy:.2f}, {gz:.2f}")
    
    def parse_json_data(self, data_str):
        try:
            data = json.loads(data_str)
            
            alpha = data.get('alpha', data.get('z', 0))
            beta = data.get('beta', data.get('x', 0))
            gamma = data.get('gamma', data.get('y', 0))
            
            gx = data.get('gx', data.get('accelerationX', 0))
            gy = data.get('gy', data.get('accelerationY', 0))
            gz = data.get('gz', data.get('accelerationZ', 0))
            
            is_recording = data.get('isRecording', False)
            frame = data.get('frame', 0)
            
            return alpha, beta, gamma, gx, gy, gz, is_recording, frame
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {data_str}")
            return None
    
    def handle_udp_connection(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.setblocking(False)
            print(f"Server listening on port {self.port}")
            
            while self.is_running:
                try:
                    data, addr = self.server_socket.recvfrom(1024)
                    parsed = self.parse_json_data(data.decode('utf-8'))
                    if parsed:
                        alpha, beta, gamma, gx, gy, gz, is_recording, frame = parsed
                        self.rotate_camera(alpha, beta, gamma, gx, gy, gz, is_recording, frame)
                except BlockingIOError:
                    time.sleep(0.001)
                except Exception as e:
                    print(f"Error: {e}")
                    
        except Exception as e:
            print(f"UDP error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def start(self):
        if self.is_running:
            print("Controller already running")
            return
        
        camera = self.get_active_camera()
        if camera:
            self.camera_base_position = list(camera.location)
        
        self.is_running = True
        print("\n" + "="*60)
        print("PROFESSIONAL CAMERA CONTROLLER v3")
        print("="*60)
        print(f"Listening on port {self.port}")
        print("Status: READY")
        print("="*60 + "\n")
        
        udp_thread = threading.Thread(target=self.handle_udp_connection, daemon=True)
        udp_thread.start()
        
        self.timer = bpy.app.timers.register(self.update_timer)
    
    def update_timer(self):
        if self.is_running:
            return 0.01
        else:
            return None
    
    def stop(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        print(f"Controller stopped. Total packets: {self.stats['packets_received']}")
        
        try:
            bpy.app.timers.unregister(self.timer)
        except:
            pass


# ============ GLOBAL INSTANCE ============
controller = None

def start_controller():
    global controller
    if controller is None:
        controller = ProfessionalCameraController()
    controller.start()

def stop_controller():
    global controller
    if controller:
        controller.stop()


# ============ PANEL UI ============

class CAMERA_CONTROLLER_PT_Panel(bpy.types.Panel):
    bl_label = "Motion Control"
    bl_idname = "CAMERA_CONTROLLER_PT_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Camera Motion Control", icon='CAMERA_DATA')
        layout.separator()
        
        if controller and controller.is_running:
            row = layout.row()
            row.label(text="Status:", icon='INFO')
            row.label(text="ACTIVE")
            
            layout.operator("wm.stop_camera_controller", text="Stop Controller", icon='CANCEL')
            layout.separator()
            
            box = layout.box()
            box.label(text="Statistics", icon='GRAPH')
            col = box.column(align=True)
            col.label(text=f"Packets: {controller.stats['packets_received']}", icon='SEQ_SEQUENCER')
            
            layout.separator()
            
            box = layout.box()
            box.label(text="Configuration", icon='PREFERENCES')
            
            row = box.row()
            row.label(text="Rotation Smoothing:")
            row.prop(context.scene, "camera_controller_rotation_smoothing", text="", slider=True)
            if context.scene.camera_controller_rotation_smoothing != controller.rotation_smoothing:
                controller.rotation_smoothing = context.scene.camera_controller_rotation_smoothing
            
            row = box.row()
            row.label(text="Position Smoothing:")
            row.prop(context.scene, "camera_controller_position_smoothing", text="", slider=True)
            if context.scene.camera_controller_position_smoothing != controller.position_smoothing:
                controller.position_smoothing = context.scene.camera_controller_position_smoothing
                
        else:
            row = layout.row()
            row.label(text="Status:", icon='INFO')
            row.label(text="INACTIVE")
            
            layout.operator("wm.start_camera_controller", text="Start Controller", icon='PLAY')


class WM_OT_StartCameraController(bpy.types.Operator):
    bl_idname = "wm.start_camera_controller"
    bl_label = "Start Camera Controller"
    
    def execute(self, context):
        start_controller()
        return {'FINISHED'}


class WM_OT_StopCameraController(bpy.types.Operator):
    bl_idname = "wm.stop_camera_controller"
    bl_label = "Stop Camera Controller"
    
    def execute(self, context):
        stop_controller()
        return {'FINISHED'}


# ============ REGISTER ============

def register():
    bpy.utils.register_class(CAMERA_CONTROLLER_PT_Panel)
    bpy.utils.register_class(WM_OT_StartCameraController)
    bpy.utils.register_class(WM_OT_StopCameraController)
    
    bpy.types.Scene.camera_controller_rotation_smoothing = bpy.props.FloatProperty(
        name="Rotation Smoothing",
        default=0.7,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.camera_controller_position_smoothing = bpy.props.FloatProperty(
        name="Position Smoothing",
        default=0.8,
        min=0.0,
        max=1.0
    )
    
    print("Camera Controller registered")


def unregister():
    stop_controller()
    bpy.utils.unregister_class(CAMERA_CONTROLLER_PT_Panel)
    bpy.utils.unregister_class(WM_OT_StartCameraController)
    bpy.utils.unregister_class(WM_OT_StopCameraController)
    
    props_to_remove = [
        "camera_controller_rotation_smoothing",
        "camera_controller_position_smoothing"
    ]
    
    for prop in props_to_remove:
        if hasattr(bpy.types.Scene, prop):
            del getattr(bpy.types.Scene, prop)


if __name__ == "__main__":
    register()
    start_controller()
    print("\nBlender Camera Controller started")
