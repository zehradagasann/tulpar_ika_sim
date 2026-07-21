# Tek bir tespit. Piksel koordinatlari YOLO'nun calistigi cozunurluge (varsayilan
# 1280x720) gore verilir; normalize alanlar cozunurlukten bagimsizdir.

# --- Sinif ---
uint16  class_id            # class_registry.yaml'daki indeks (0..14)
string  class_name          # okunabilirlik icin, ornek: "dusman_hava_araci"
float32 confidence          # 0.0 - 1.0

# --- Takip (DeepSORT icin ayrildi; takip yokken 0) ---
uint32  track_id            # 0 = takip edilmiyor
uint32  age                 # kac ardisik karedir goruluyor

# --- 2B kutu, piksel ---
float32 center_x
float32 center_y
float32 width
float32 height

# --- 2B kutu, normalize (0.0 - 1.0) ---
float32 center_x_norm
float32 center_y_norm
float32 width_norm
float32 height_norm

# --- 3B konum (metre, camera_link: X saga, Y asagi, Z ileri) ---
# has_position=false iken position_* ANLAMSIZDIR. RealSense gelene kadar daima false.
bool    has_position
float32 position_x
float32 position_y
float32 position_z
float32 position_stddev     # metre, bilinmiyorsa 0

# --- PID / atis mantigi icin turetilmis alanlar ---
# Goruntu merkezine gore hata, normalize (-1.0 .. +1.0)
float32 error_x
float32 error_y
bool    in_shooting_zone
