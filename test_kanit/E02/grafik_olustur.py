#!/usr/bin/env python3
import matplotlib.pyplot as plt
import csv

zaman, konum, hiz = [], [], []

with open('/home/talha/tulpar_ika_sim/test_kanit/E02/hizlanma_verisi.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        zaman.append(float(row['zaman']))
        konum.append(float(row['konum_x']))
        hiz.append(float(row['hiz']))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9))

# Konum-zaman grafiği
ax1.plot(zaman, konum, 'b-', linewidth=2)
ax1.set_xlabel('Zaman (s)', fontsize=11)
ax1.set_ylabel('Konum X (m)', fontsize=11)
ax1.set_title('E-02: Tulpar İKA — 30 m Hızlanma Parkuru Konum-Zaman Grafiği', fontsize=12, fontweight='bold')
ax1.axhline(y=30, color='r', linestyle='--', label='30 m hedef mesafe')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=10)

# Hız-zaman grafiği
ax2.plot(zaman, hiz, 'r-', linewidth=2)
ax2.set_xlabel('Zaman (s)', fontsize=11)
ax2.set_ylabel('Doğrusal Hız (m/s)', fontsize=11)
ax2.set_title('E-02: Tulpar İKA — Hız-Zaman Grafiği', fontsize=12, fontweight='bold')
ax2.axhline(y=0.5, color='g', linestyle='--', label='Hedef hız: 0.5 m/s')
ax2.set_ylim(0, 0.7)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=10)

plt.tight_layout()
plt.savefig('/home/talha/tulpar_ika_sim/test_kanit/E02/E02_hizlanma_grafigi.png', dpi=150)
print('Grafik kaydedildi: E02_hizlanma_grafigi.png')

# Özet istatistik
print(f'\n--- E-02 TEST SONUÇLARI ---')
print(f'Toplam süre: {zaman[-1]:.2f} s')
print(f'Kat edilen mesafe: {konum[-1]:.2f} m')
print(f'Ortalama hız: {konum[-1]/zaman[-1]:.4f} m/s')
print(f'Maksimum hız: {max(hiz):.4f} m/s')