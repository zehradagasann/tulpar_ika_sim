uint8 ACTION_UNKNOWN=0
uint8 ACTION_STOP=1
uint8 ACTION_SPEED_LIMIT=2
uint8 ACTION_SLOW_DOWN=3
uint8 ACTION_TURN_LEFT=4
uint8 ACTION_TURN_RIGHT=5
uint8 ACTION_WATER=6
uint8 ACTION_ROUGH_TERRAIN=7
uint8 ACTION_UNEVEN_TERRAIN=8

uint16 class_id
string class_name
float32 confidence

sensor_msgs/RegionOfInterest bbox
geometry_msgs/Point32 center_px

float32 distance_m
bool distance_valid

uint8 action

float32 speed_limit_mps
bool speed_limit_valid
