import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import csv

zaman, mesafe, sapma, lazer = [], [], [], []

with open('/home/talha/tulpar_ika_sim/test_kanit/S02/s02_hedef_verisi.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        zaman.append(float(row['zaman']))
        mesafe.append(float(row['mesafe']))
        sapma.append(float(row['sapma_derece']))
        lazer.append(int(row['lazer_aktif']))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9))

# Lazer aktif olduğu bölgeyi renklendir
lazer_baslangic = next((z for z, l in zip(zaman, lazer) if l == 1), None)
if lazer_baslangic is not None:
    ax1.axvspan(lazer_baslangic, zaman[-1], alpha=0.15, color='red', label='Lazer AKTİF')
    ax2.axvspan(lazer_baslangic, zaman[-1], alpha=0.15, color='red', label='Lazer AKTİF')

ax1.plot(zaman, mesafe, 'b-', linewidth=2, label='Hedefe mesafe (m)')
ax1.axhline(y=10.0, color='orange', linestyle='--', label='Hedef mesafe: 10 m')
ax1.set_xlabel('Zaman (s)', fontsize=11)
ax1.set_ylabel('Mesafe (m)', fontsize=11)
ax1.set_title('S-02: Tulpar İKA — Hedef Tespit ve Kilitlenme Simülasyonu\nMesafe-Zaman Grafiği',
              fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=10)

ax2.plot(zaman, sapma, 'r-', linewidth=2, label='Açısal sapma (°)')
ax2.axhline(y=2.0,  color='g', linestyle='--', alpha=0.7, label='+2° tolerans')
ax2.axhline(y=-2.0, color='g', linestyle='--', alpha=0.7, label='-2° tolerans')
ax2.axhline(y=0.0,  color='k', linestyle='-',  alpha=0.3, label='Merkez')
ax2.fill_between(zaman, -2, 2, alpha=0.1, color='green', label='Merkez bölgesi ±2°')
ax2.set_xlabel('Zaman (s)', fontsize=11)
ax2.set_ylabel('Açısal Sapma (°)', fontsize=11)
ax2.set_title('S-02: Hedef Merkez Sapması ve Kilit Durumu', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=10)

plt.tight_layout()
out = '/home/talha/tulpar_ika_sim/test_kanit/S02/S02_hedef_grafigi.png'
plt.savefig(out, dpi=150)
print(f'Grafik kaydedildi: {out}')

print('\n--- S-02 TEST SONUÇLARI ---')
print(f'Ortalama mesafe  : {sum(mesafe)/len(mesafe):.3f} m')
print(f'Ortalama sapma   : {sum(abs(s) for s in sapma)/len(sapma):.3f}°')
print(f'Max sapma        : {max(abs(s) for s in sapma):.3f}°')
lazer_sure = sum(1 for l in lazer if l) * (zaman[-1] - zaman[0]) / len(zaman) if len(zaman) > 1 else 0
print(f'Lazer aktif süre : ~{lazer_sure:.2f} s')

plt.show()
