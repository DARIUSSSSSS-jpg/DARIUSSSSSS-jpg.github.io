"""
BLENDER CAMERA CONTROLLER v3.1 - Professional Edition
Controla la cámara 3D en Blender en tiempo real desde el móvil
Soporta: Rotación + Acelerómetro + Duración dinámica de frames + Motion Capture Pro

INSTALACIÓN:
1. Blender > Scripting > New
2. Copiar este código
3. Alt + P para ejecutar

REQUISITOS:
- Blender 3.0+
- Python 3.9+
- Red local (Wi-Fi) con acceso a puerto 5005
"""

import bpy
import json
import math
import threading
import socket
from collections import deque
import time
from datetime import datetime
import logging

# ============ LOGGING SETUP ============
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class ProfessionalCameraController:
    """
    Controlador profesional de cámara para Blender.
    Gestiona conexión UDP/WebSocket y motion capture en tiempo real.
    """

    def __init__(self):
        self.is_running = False
        self.server_socket = None
        
        # ============ SMOOTHING PARAMETERS ============
        self.rotation_smoothing = 0.7
        self.position_smoothing = 0.8
        self.last_rotation = [0, 0, 0]
        self.last_position = [0, 0, 0]
        
        # ============ NETWORK CONFIG ============
        self.port = 5005
        self.host = '0.0.0.0'
        
        # ============ MOTION HISTORY ============
        self.rotation_history = deque(maxlen=10)
        self.position_history = deque(maxlen=10)
        
        # ============ CAMERA PARAMS ============
        self.position_scale = 0.1
        self.camera_base_position = [0, 0, 0]
        self.is_recording = False
        self.current_frame = 0
        self.max_frames = 100
        self.axis_locked = {'X': False, 'Y': False, 'Z': False}
        
        # ============ STATISTICS ============
        self.stats = {
            'packets_received': 0,
            'last_update': 0,
            'fps': 0,
            'frame_count': 0,
            'last_acceleration': [0, 0, 0],
            'connection_start': None,
            'uptime_seconds': 0
        }
        
        # ============ TIMER ============
        self.timer = None
        
    def get_active_camera(self):
        """Obtiene la cámara activa de la escena."""
        try:
            camera = bpy.context.scene.camera
            if not camera:
                logger.warning("⚠ No hay cámara activa en la escena")
                return None
            return camera
        except Exception as e:
            logger.error(f"✗ Error obteniendo cámara: {e}")
            return None
    
    def apply_rotation_smoothing(self, new_rotation):
        """Aplica suavizado exponencial a la rotación."""
        try:
            smoothed = [
                self.last_rotation[i] * self.rotation_smoothing + 
                new_rotation[i] * (1 - self.rotation_smoothing)
                for i in range(3)
            ]
            self.last_rotation = smoothed
            return smoothed
        except Exception as e:
            logger.error(f"✗ Error en suavizado de rotación: {e}")
            return new_rotation
    
    def apply_position_smoothing(self, new_position):
        """Aplica suavizado exponencial a la posición."""
        try:
            smoothed = [
                self.last_position[i] * self.position_smoothing + 
                new_position[i] * (1 - self.position_smoothing)
                for i in range(3)
            ]
            self.last_position = smoothed
            return smoothed
        except Exception as e:
            logger.error(f"✗ Error en suavizado de posición: {e}")
            return new_position
    
    def rotate_camera(self, alpha, beta, gamma, gx=0, gy=0, gz=0, 
                      is_recording=False, frame=0, axis_locked=None):
        """
        Aplica rotación y posición a la cámara activa.
        
        Args:
            alpha: Rotación Z (0-360°)
            beta: Inclinación X (-180 a 180°)
            gamma: Inclinación Y (-90 a 90°)
            gx, gy, gz: Aceleración del acelerómetro
            is_recording: Si está grabando keyframes
            frame: Frame actual
            axis_locked: Dict con ejes bloqueados
        """
        camera = self.get_active_camera()
        if not camera:
            return
        
        try:
            # ============ ROTACIÓN CON CORRECCIÓN DE EJES ============
            x_rad = -math.radians(beta) if not (axis_locked and axis_locked.get('X')) else camera.rotation_euler[0]
            y_rad = -math.radians(gamma) if not (axis_locked and axis_locked.get('Y')) else camera.rotation_euler[1]
            z_rad = math.radians(alpha) if not (axis_locked and axis_locked.get('Z')) else camera.rotation_euler[2]
            
            smoothed_rotation = self.apply_rotation_smoothing([x_rad, y_rad, z_rad])
            
            camera.rotation_euler[0] = smoothed_rotation[0]
            camera.rotation_euler[1] = smoothed_rotation[1]
            camera.rotation_euler[2] = smoothed_rotation[2]
            
            # ============ POSICIÓN DESDE ACELERÓMETRO ============
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
            
            # ============ KEYFRAMES SI ESTÁ GRABANDO ============
            if is_recording and bpy.context.scene.is_animation_playing:
                try:
                    camera.keyframe_insert(data_path="rotation_euler", frame=frame)
                    camera.keyframe_insert(data_path="location", frame=frame)
                except Exception as e:
                    logger.debug(f"No se pudo insertar keyframe: {e}")
            
            # ============ ESTADÍSTICAS ============
            self.stats['packets_received'] += 1
            self.stats['frame_count'] += 1
            self.stats['last_update'] = time.time()
            
            # Log cada 20 frames
            if self.stats['frame_count'] % 20 == 0:
                logger.info(
                    f"Frame {frame}/{self.max_frames} | "
                    f"Rot: A={alpha:.0f}° B={beta:.0f}° G={gamma:.0f}° | "
                    f"Acc: ({gx:.2f}, {gy:.2f}, {gz:.2f})"
                )
                
        except Exception as e:
            logger.error(f"✗ Error en rotate_camera: {e}")
    
    def parse_json_data(self, data_str):
        """
        Parsea datos JSON del cliente móvil.
        Soporta múltiples formatos de datos.
        """
        try:
            data = json.loads(data_str)
            
            # Compatibilidad con múltiples formatos
            alpha = data.get('alpha', data.get('z', 0))
            beta = data.get('beta', data.get('x', 0))
            gamma = data.get('gamma', data.get('y', 0))
            
            gx = data.get('gx', data.get('accelerationX', 0))
            gy = data.get('gy', data.get('accelerationY', 0))
            gz = data.get('gz', data.get('accelerationZ', 0))
            
            is_recording = data.get('isRecording', False)
            frame = data.get('frame', 0)
            axis_locked = data.get('axisLocked', {})
            
            return alpha, beta, gamma, gx, gy, gz, is_recording, frame, axis_locked
            
        except json.JSONDecodeError as e:
            logger.error(f"✗ Error decodificando JSON: {data_str} | {e}")
            return None
    
    def handle_udp_connection(self):
        """Maneja la conexión UDP y recepción de datos."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.setblocking(False)
            
            logger.info(f"✓ Servidor escuchando en puerto {self.port}")
            self.stats['connection_start'] = datetime.now()
            
            while self.is_running:
                try:
                    data, addr = self.server_socket.recvfrom(1024)
                    parsed = self.parse_json_data(data.decode('utf-8'))
                    
                    if parsed:
                        alpha, beta, gamma, gx, gy, gz, is_recording, frame, axis_locked = parsed
                        self.rotate_camera(
                            alpha, beta, gamma, gx, gy, gz, 
                            is_recording, frame, axis_locked
                        )
                except BlockingIOError:
                    time.sleep(0.001)
                except Exception as e:
                    logger.debug(f"Error procesando paquete: {e}")
                    
        except Exception as e:
            logger.error(f"✗ Error UDP: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                logger.info("✓ Socket cerrado")
    
    def start(self):
        """Inicia el controlador."""
        if self.is_running:
            logger.warning("⚠ Controlador ya está ejecutándose")
            return
        
        camera = self.get_active_camera()
        if camera:
            self.camera_base_position = list(camera.location)
        else:
            logger.warning("⚠ No se encontró cámara activa")
        
        self.is_running = True
        
        logger.info("=" * 70)
        logger.info("PROFESSIONAL CAMERA CONTROLLER v3.1")
        logger.info("=" * 70)
        logger.info(f"🎬 Escuchando en {self.host}:{self.port}")
        logger.info(f"📱 Conecta tu móvil a: http://[TU_IP]:{self.port}")
        logger.info("Status: ✓ READY")
        logger.info("=" * 70)
        
        # Iniciar thread UDP
        udp_thread = threading.Thread(
            target=self.handle_udp_connection, 
            daemon=True,
            name="CameraController-UDP"
        )
        udp_thread.start()
        
        # Registrar timer
        if self.timer is None:
            self.timer = bpy.app.timers.register(self.update_timer)
    
    def update_timer(self):
        """Timer callback para updates periódicos."""
        if self.is_running:
            # Calcular uptime
            if self.stats['connection_start']:
                delta = datetime.now() - self.stats['connection_start']
                self.stats['uptime_seconds'] = delta.total_seconds()
            return 0.01
        else:
            return None
    
    def stop(self):
        """Detiene el controlador."""
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("=" * 70)
        logger.info(f"✓ Controlador detenido")
        logger.info(f"📊 Paquetes recibidos: {self.stats['packets_received']}")
        logger.info(f"⏱ Tiempo activo: {self.stats['uptime_seconds']:.1f}s")
        logger.info("=" * 70)
        
        try:
            if self.timer:
                bpy.app.timers.unregister(self.timer)
                self.timer = None
        except Exception as e:
            logger.debug(f"Error deregistrando timer: {e}")


# ============ GLOBAL INSTANCE ============
controller = None


def start_controller():
    """Inicia instancia global del controlador."""
    global controller
    if controller is None:
        controller = ProfessionalCameraController()
    controller.start()


def stop_controller():
    """Detiene instancia global del controlador."""
    global controller
    if controller:
        controller.stop()


# ============ PANEL UI ============

class CAMERA_CONTROLLER_PT_Panel(bpy.types.Panel):
    """Panel de control en propiedades de escena."""
    bl_label = "Motion Control"
    bl_idname = "CAMERA_CONTROLLER_PT_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="🎥 Camera Motion Control", icon='CAMERA_DATA')
        layout.separator()
        
        if controller and controller.is_running:
            # ============ STATUS ACTIVE ============
            row = layout.row()
            row.label(text="Estado:", icon='INFO')
            row.label(text="✓ ACTIVO", icon='PLAY')
            
            layout.operator("wm.stop_camera_controller", 
                          text="⏹ Detener Controlador", icon='CANCEL')
            layout.separator()
            
            # ============ STATISTICS ============
            box = layout.box()
            box.label(text="📊 Estadísticas", icon='GRAPH')
            col = box.column(align=True)
            col.label(text=f"Paquetes: {controller.stats['packets_received']}", 
                     icon='SEQ_SEQUENCER')
            col.label(text=f"Frames: {controller.stats['frame_count']}", 
                     icon='PREVIEW_RANGE')
            col.label(text=f"Uptime: {controller.stats['uptime_seconds']:.1f}s", 
                     icon='TIME')
            
            layout.separator()
            
            # ============ CONFIGURATION ============
            box = layout.box()
            box.label(text="⚙ Configuración", icon='PREFERENCES')
            
            row = box.row()
            row.label(text="Suavizado Rotación:")
            row.prop(context.scene, "camera_controller_rotation_smoothing", 
                    text="", slider=True)
            if context.scene.camera_controller_rotation_smoothing != controller.rotation_smoothing:
                controller.rotation_smoothing = context.scene.camera_controller_rotation_smoothing
            
            row = box.row()
            row.label(text="Suavizado Posición:")
            row.prop(context.scene, "camera_controller_position_smoothing", 
                    text="", slider=True)
            if context.scene.camera_controller_position_smoothing != controller.position_smoothing:
                controller.position_smoothing = context.scene.camera_controller_position_smoothing
                
        else:
            # ============ STATUS INACTIVE ============
            row = layout.row()
            row.label(text="Estado:", icon='INFO')
            row.label(text="✗ INACTIVO", icon='PAUSE')
            
            layout.operator("wm.start_camera_controller", 
                          text="▶ Iniciar Controlador", icon='PLAY')


class WM_OT_StartCameraController(bpy.types.Operator):
    """Operador para iniciar controlador."""
    bl_idname = "wm.start_camera_controller"
    bl_label = "Start Camera Controller"
    bl_description = "Inicia el controlador de cámara Motion Capture"
    
    def execute(self, context):
        start_controller()
        return {'FINISHED'}


class WM_OT_StopCameraController(bpy.types.Operator):
    """Operador para detener controlador."""
    bl_idname = "wm.stop_camera_controller"
    bl_label = "Stop Camera Controller"
    bl_description = "Detiene el controlador de cámara Motion Capture"
    
    def execute(self, context):
        stop_controller()
        return {'FINISHED'}


# ============ REGISTER/UNREGISTER ============

def register():
    """Registra clases y propiedades."""
    try:
        bpy.utils.register_class(CAMERA_CONTROLLER_PT_Panel)
        bpy.utils.register_class(WM_OT_StartCameraController)
        bpy.utils.register_class(WM_OT_StopCameraController)
        
        # Propiedades de escena
        bpy.types.Scene.camera_controller_rotation_smoothing = bpy.props.FloatProperty(
            name="Rotation Smoothing",
            description="Suavizado de rotación (0-1, mayor = más suave)",
            default=0.7,
            min=0.0,
            max=1.0,
            step=0.1
        )
        
        bpy.types.Scene.camera_controller_position_smoothing = bpy.props.FloatProperty(
            name="Position Smoothing",
            description="Suavizado de posición (0-1, mayor = más suave)",
            default=0.8,
            min=0.0,
            max=1.0,
            step=0.1
        )
        
        logger.info("✓ Motion Control Addon registrado correctamente")
        
    except Exception as e:
        logger.error(f"✗ Error durante registro: {e}")


def unregister():
    """Desregistra clases y propiedades."""
    try:
        stop_controller()
        
        bpy.utils.unregister_class(CAMERA_CONTROLLER_PT_Panel)
        bpy.utils.unregister_class(WM_OT_StartCameraController)
        bpy.utils.unregister_class(WM_OT_StopCameraController)
        
        # Remover propiedades
        props_to_remove = [
            "camera_controller_rotation_smoothing",
            "camera_controller_position_smoothing"
        ]
        
        for prop in props_to_remove:
            if hasattr(bpy.types.Scene, prop):
                del getattr(bpy.types.Scene, prop)
        
        logger.info("✓ Motion Control Addon desregistrado correctamente")
        
    except Exception as e:
        logger.error(f"✗ Error durante desregistro: {e}")


if __name__ == "__main__":
    register()
    start_controller()
    logger.info("🚀 Blender Camera Controller iniciado")
