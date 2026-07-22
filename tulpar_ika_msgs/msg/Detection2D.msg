uint8 SOURCE_UNKNOWN=0
uint8 SOURCE_OPENCV=1
uint8 SOURCE_YOLO=2
uint8 SOURCE_FUSED=3

uint16 class_id
string class_name
float32 confidence

sensor_msgs/RegionOfInterest bbox
geometry_msgs/Point32 center_px

float32 depth_m
bool depth_valid

uint32 track_id
bool track_id_valid

uint8 source
