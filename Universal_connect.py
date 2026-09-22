import rtde_control
import rtde_receive
import rtde_io
import numpy as np
import copy
import time

from robotcontrol import URControl


robot_ip = "192.168.0.43"  # replace with your robot's IP address, see [How to find and set the IP address for connecting a PC to a UR robot](/t/how-to-find-and-set-the-ip-address-for-connecting-a-pc-to-a-ur-robot/4721)

home = [0.469, -0.259, 0.098, 1.158, 2.911, -0.041]

robot = URControl(robot_ip)
robot.connect()

loca = robot.get_tcp_pos()
#print(loca)


end_waste = 0.01
breedte = 0.1
begin_afstand = 0.01

acceleration = 1
smoothness = 0.001 # Cirkel om node heen waar pad doorheen wordt gesmooth (blend radius voor xy veranderingen)
curve = 0.002 # Blend radius voor Z verandering

# Variabelen die vastgesteld moeten worden
bulb_breedte = 0.02
bulb_hoogtepunt_breedte = 0.01
snelheid_per_dikte = {0.004:0.3, 0.005:0.02, 0.006:0.15, 0.008:0.1, 0.01:0.05}

# Alles relatief aan punt [0,0] tegen muur aan eind balk
# Type0 Cut

pad0 = []
pad0.append([-end_waste, breedte+begin_afstand])
pad0.append([-end_waste, -begin_afstand])


# Type6 Cut
Y = 10 # In degrees

pad6 = []
pad6.append([-end_waste-0.006-begin_afstand, breedte+begin_afstand])
pad6.append([-end_waste, breedte-0.006])
pad6.append([-np.tan(Y*np.pi/180)*(breedte-0.006+begin_afstand), -begin_afstand])



def plat_profiel(nulpunt, pad2d, dikte):
    '''Maakt van de 2d coordinaten een uitvoerbaar 'path' met alle 6 assen, blend op de juiste plekken en snelheid'''
    speed = snelheid_per_dikte[dikte]
    pad = []
    for node in pad2d:
        coordinaat = nulpunt.copy()
        coordinaat[0] += node[0]
        coordinaat[1] += node[1]
        coordinaat[2] += dikte
        coordinaat.append(speed)
        coordinaat.append(acceleration)
        coordinaat.append(smoothness)

        pad.append(coordinaat)

    pad[0][8] = 0 # start en eind punt met 0 blend
    pad[-1][8] = 0
    return pad



def hp_profiel(nulpunt, pad2d, dikte):
    '''Maakt van de 2d coordinaten een uitvoerbaar 'path' met alle 6 assen, blend op de juiste plekken en snelheid'''
    speed = snelheid_per_dikte[dikte]
    pad = []
    bulb_hoogte = 3*dikte

    for i in range(len(pad2d)):
        coordinaat = nulpunt.copy()
        coordinaat[0] += pad2d[i][0]
        coordinaat[1] += pad2d[i][1]
        if pad2d[i][1] < bulb_breedte:
            coordinaat[2] += bulb_hoogte
            coordinaat.append(speed/3)
        else:
            coordinaat[2] += dikte
            coordinaat.append(speed)
        coordinaat.append(acceleration)
        coordinaat.append(smoothness)
                
        pad.append(coordinaat)

       
        if pad2d[i][1] < bulb_breedte-curve and pad2d[i-1][1] > bulb_breedte+curve:
            i1 = i
            c1 = nulpunt.copy()
            vector1 = ((bulb_breedte)-pad2d[i-1][1])/(pad2d[i][1]-pad2d[i-1][1])
            c1[0] += pad2d[i-1][0] + vector1*(pad2d[i][0]-pad2d[i-1][0])
            c1[1] += bulb_breedte
            c1[2] += dikte
            c1.append(speed)
            c1.append(acceleration)
            c1.append(curve)

        
        if pad2d[i][1] < bulb_hoogtepunt_breedte-curve and pad2d[i-1][1] > bulb_hoogtepunt_breedte+curve:
            i2 = i
            c2 = nulpunt.copy()
            vector2 = ((bulb_breedte)-pad2d[i-1][1])/(pad2d[i][1]-pad2d[i-1][1])
            c2[0] += pad2d[i-1][0] + vector2*(pad2d[i][0]-pad2d[i-1][0])
            c2[1] += bulb_hoogtepunt_breedte
            c2[2] += bulb_hoogte
            c2.append(speed/3)
            c2.append(acceleration)
            c2.append(curve)

    if 'i2' in locals():
        pad.insert(i2, c2)

    if 'i1' in locals():
        pad.insert(i1, c1)

    pad[0][8] = 0 # start en eind punt met 0 blend
    pad[-1][8] = 0

    return pad


# Testen
arm_volgt = hp_profiel(home, pad6, 0.005)

print('arm', arm_volgt)

hoge_home = home.copy()
hoge_home[2] += 0.05

robot.move_l(hoge_home, 0.1)
robot.move_l(arm_volgt[0][:6], 0.1)
time.sleep(1)
robot.move_l_path(arm_volgt)
time.sleep(1)
robot.move_l(hoge_home, 0.05)

robot.stop_robot_control()
