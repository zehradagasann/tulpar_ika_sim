import matplotlib.pyplot as plt
import csv
import pathlib
_DIR = pathlib.Path(__file__).parent

zaman, mesafe, konum_y, hiz_x, hiz_y = [], [], [], [], []

with open(_DIR / 's01_odom_verisi.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        zaman.append(float(row['zaman']))
        mesafe.append(float(row['mesafe_x']))
        konum_y.append(float(row['konum_y']))
        hiz_x.append(float(row['hiz_x']))
        hiz_y.append(float(row['hiz_y']))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9))

ax1.plot(zaman, mesafe, 'b-', linewidth=2, label='X mesafesi')
ax1.set_xlabel('Zaman (s)', fontsize=11)
ax1.set_ylabel('Mesafe (m)', fontsize=11)
ax1.set_title('S-01: Tulpar İKA — Dinamik Zemin Simülasyonu Mesafe Grafiği', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=10)

# Engel konumları
ax1.axvline(x=6, color='orange', linestyle='--', alpha=0.7, label='Rampa %45')
ax1.axvline(x=14, color='blue', linestyle='--', alpha=0.7, label='Yan egim %20')
ax1.axvline(x=22, color='red', linestyle='--', alpha=0.7, label='Blok 15cm')
ax1.axvline(x=28, color='gray', linestyle='--', alpha=0.7, label='Tumsekler')
ax1.legend(fontsize=9)

ax2.plot(zaman, hiz_x, 'r-', linewidth=2, label='İleri hız (m/s)')
ax2.plot(zaman, hiz_y, 'g-', linewidth=1.5, alpha=0.7, label='Yan hız (m/s)')
ax2.set_xlabel('Zaman (s)', fontsize=11)
ax2.set_ylabel('Hız (m/s)', fontsize=11)
ax2.set_title('S-01: Tulpar İKA — Hız Profili (Engel Etkileşimleri)', fontsize=12, fontweight='bold')
ax2.axhline(y=0.5, color='g', linestyle='--', alpha=0.5, label='Hedef hız')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=10)

plt.tight_layout()
plt.savefig(_DIR / 'S01_zemin_grafigi.png', dpi=150)
print('Grafik kaydedildi!')
print(f'\n--- S-01 TEST SONUÇLARI ---')
print(f'Toplam sure: {zaman[-1]:.2f} s')
print(f'Kat edilen mesafe: {mesafe[-1]:.2f} m')
print(f'Max yan sapma: {max(abs(y) for y in konum_y):.4f} m')
plt.show()