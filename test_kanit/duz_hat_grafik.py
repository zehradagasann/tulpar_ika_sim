#!/usr/bin/env python3
"""duz_hat_testi.py'nin ciktisi olan CSV'yi cizer.

Kullanim: python3 test_kanit/duz_hat_grafik.py [csv_dosyasi]
"""
import csv
import sys

import matplotlib.pyplot as plt


def main():
    dosya = sys.argv[1] if len(sys.argv) > 1 else 'duz_hat_sonuc.csv'

    t, x, y, vx, wz, pitch = [], [], [], [], [], []
    with open(dosya) as f:
        for row in csv.DictReader(f):
            t.append(float(row['t_sn']))
            x.append(float(row['x']))
            y.append(float(row['y']))
            vx.append(float(row['linear_x']))
            wz.append(float(row['angular_z']))
            pitch.append(float(row['pitch_rad']))

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))

    axes[0, 0].plot(x, y)
    axes[0, 0].set_title('Yörünge (x-y)')
    axes[0, 0].set_xlabel('x (m)')
    axes[0, 0].set_ylabel('y (m)')
    axes[0, 0].axis('equal')

    axes[0, 1].plot(t, vx)
    axes[0, 1].set_title('İleri hız (linear.x)')
    axes[0, 1].set_xlabel('t (s)')
    axes[0, 1].set_ylabel('m/s')

    axes[1, 0].plot(t, wz)
    axes[1, 0].set_title('Açısal hız (angular.z)')
    axes[1, 0].set_xlabel('t (s)')
    axes[1, 0].set_ylabel('rad/s')

    axes[1, 1].plot(t, pitch)
    axes[1, 1].set_title('IMU Pitch')
    axes[1, 1].set_xlabel('t (s)')
    axes[1, 1].set_ylabel('rad')

    fig.tight_layout()
    png = dosya.replace('.csv', '.png')
    fig.savefig(png, dpi=120)
    print(f'Grafik kaydedildi: {png}')


if __name__ == '__main__':
    main()
