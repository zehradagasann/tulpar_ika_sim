# Bir kareden cikan tum tespitler. /detections topic'inde yayinlanir.

std_msgs/Header header      # stamp = karenin YAKALANMA ani (islenme ani degil)
                            # frame_id = "camera_link" (Zehra'nin URDF'iyle uyumlu)

uint32  frame_seq           # kamera node'unun kare sayaci
uint16  image_width         # tespitlerin uretildigi genislik (or. 1280)
uint16  image_height        # or. 720
float32 inference_ms        # bu kare icin YOLO suresi, teshis amacli

Detection[] detections      # bos olabilir
