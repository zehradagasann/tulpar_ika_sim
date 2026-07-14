import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
import pathlib
_DIR = pathlib.Path(__file__).parent

zaman, x, z, roll, pitch = [], [], [], [], []

with open(_DIR / 's01_tam_parkur_verisi.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        zaman.append(float(row['zaman']))
        x.append(float(row['konum_x']))
        z.append(float(row['konum_z']))
        roll.append(float(row['roll']))
        pitch.append(float(row['pitch']))

fig, axes = plt.subplots(3, 1, figsize=(12, 12))

# Engel bölgesi renkleri
bolge = [
    (2.0,  7.5,  '#FF8C00', 'Rampa (45cm, 20b)'),
    (9.0,  13.5, '#1E90FF', '%20 Yan Eğim'),
    (14.5, 16.0, '#DC143C', '15cm Blok'),
    (16.8, 21.5, '#696969', '5cm Tümsekler'),
]

for ax in axes:
    for x0, x1, c, lbl in bolge:
        ts = [zaman[i] for i, v in enumerate(x) if x0 <= v <= x1]
        if ts:
            ax.axvspan(ts[0], ts[-1], alpha=0.12, color=c, label=lbl)

# 1. X konumu
axes[0].plot(zaman, x, 'b-', linewidth=2, label='X konumu (m)')
axes[0].set_ylabel('Konum X (m)', fontsize=10)
axes[0].set_title('S-01: Tulpar İKA — Dinamik Zemin Parkuru\nX Konumu', fontsize=12, fontweight='bold')
axes[0].grid(True, alpha=0.3); axes[0].legend(fontsize=9)

# 2. Roll
axes[1].plot(zaman, roll, 'g-', linewidth=2, label='Roll (°)')
axes[1].axhline(y=20,  color='orange', linestyle='--', alpha=0.7, label='+20° yan eğim')
axes[1].axhline(y=-20, color='orange', linestyle='--', alpha=0.7)
axes[1].axhline(y=0,   color='k', linestyle='-', alpha=0.2)
axes[1].set_ylabel('Roll (°)', fontsize=10)
axes[1].set_title('Roll Açısı (Yan Devrilme)', fontsize=11, fontweight='bold')
axes[1].grid(True, alpha=0.3); axes[1].legend(fontsize=9)

# 3. Pitch
axes[2].plot(zaman, pitch, 'r-', linewidth=2, label='Pitch (°)')
axes[2].axhline(y=12.7,  color='orange', linestyle='--', alpha=0.7, label='+12.7° (rampa eğimi)')
axes[2].axhline(y=-12.7, color='orange', linestyle='--', alpha=0.7)
axes[2].axhline(y=0,     color='k', linestyle='-', alpha=0.2)
axes[2].set_xlabel('Zaman (s)', fontsize=10)
axes[2].set_ylabel('Pitch (°)', fontsize=10)
axes[2].set_title('Pitch Açısı (Öne-Arkaya Eğim)', fontsize=11, fontweight='bold')
axes[2].grid(True, alpha=0.3); axes[2].legend(fontsize=9)

plt.tight_layout()
out = _DIR / 'S01_tam_parkur_grafigi.png'
plt.savefig(out, dpi=150)
print(f'Grafik kaydedildi: {out}')

print('\n--- S-01 TAM PARKUR SONUÇLARI ---')
print(f'Toplam süre      : {zaman[-1]:.2f} s')
print(f'Son konum X      : {x[-1]:.3f} m')
print(f'Max roll         : {max(abs(r) for r in roll):.2f}°')
print(f'Max pitch        : {max(abs(p) for p in pitch):.2f}°')
print(f'Max Z yüksekliği : {max(z):.4f} m')
