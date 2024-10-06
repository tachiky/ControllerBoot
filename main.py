import network
import utime
import uping
import socket
import machine

import bluetooth
import blegamepad

# Wi-Fi接続設定
SSID = '<Wi-Fi SSID>'
PW = '<Wi-Fi Password>'
# XBOXコントローラ MACアドレス
# 書式は'XX:XX:XX:XX:XX:XX'
XBOX_MACADDR = 'XX:XX:XX:XX:XX:XX'
# PCのIPアドレス
PC_IPADDR = 'yyy.yyy.yyy.yyy'
# PCのMACアドレス
# 書式は[0xZZ,0xZZ,0xZZ,0xZZ,0xZZ,0xZZ]
PC_MACADDR = [0xZZ,0xZZ,0xZZ,0xZZ,0xZZ,0xZZ]
# PCの終了後、XBOXコントローラの再検知を実行しない時間(秒)
GRACETIME = 180

led = machine.Pin("LED", machine.Pin.OUT)

# マジックパケット送信関数
def send_magicpacket(mac):
    msg = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]
    wol_port = 9
    magic = msg + (mac * 16)
    print('Send WoL Magic Packet.')
    try:
        soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        soc.sendto(bytes(magic),("255.255.255.255",wol_port))
    finally:
        soc.close()

def connect_wifi(wlan):
    wlan.connect(SSID, PW)

    while wlan.isconnected() == False:
        print('Connecting to Wi-Fi router')
        utime.sleep(1)

    wlan_status = wlan.ifconfig()
    print('Connected!')
    print(f'IP Address: {wlan_status[0]}')
    print(f'Netmask: {wlan_status[1]}')
    print(f'Default Gateway: {wlan_status[2]}')
    print(f'Name Server: {wlan_status[3]}')
    # Wi-Fi接続中はLEDをONにする
    led.on()

### メイン処理（無限ループ）
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
connect_wifi(wlan)
ble = bluetooth.BLE()
while True:
    # ループの先頭でblegamepad.gamepadを宣言
    pad = blegamepad.gamepad(ble, XBOX_MACADDR)
    ### コントローラの起動待ち
    # BLEのスキャンでXBOXコントローラを検索
    while not pad.is_find_controller():
        #print('loop')
        if wlan.isconnected() == False:
            print('Wi-Fi is not connected. Connecting...')
            connect_wifi(wlan)
        else:
            led.on()
        pad.scan()
        while pad.is_scanning():
            utime.sleep(0.1)
    print('Controller Find.')

    #ループを抜けた＝コントローラを見つけた状態なのでWoL用マジックパケットを送信
    send_magicpacket(PC_MACADDR)

    ### PCの起動中
    # 10秒間ごとにPCに対しpingし、応答なければWoL実行を繰り返す
    bootup_flg = True
    while bootup_flg:
        # 10秒間LEDを点滅させながら待機
        countdown = 10
        while countdown > 0:
            # LEDの点滅間隔は1秒
            led.on()
            utime.sleep(0.5)
            led.off()
            utime.sleep(0.5)
            countdown -= 1
        # pingして疎通確認
        res = uping.ping(PC_IPADDR, count=1)
        if res == (1, 1):
            print('PC is running.')
            bootup_flg = False
        else:
            print('PC is not running. Re-send Magic Packet.')
            send_magicpacket(PC_MACADDR)

    ### 起動完了状態
    # 10秒ごとに疎通確認する
    # LEDは点灯状態とする
    led.on()
    running_flg = True
    while running_flg:
        utime.sleep(10)
        res = uping.ping(PC_IPADDR, count=1)
        if res == (1, 1):
            print('PC is running.')
        else:
            print('PC is shutting down')
            running_flg = False

    ### 終了待機
    # この時間、XBOXコントローラの検出があってもWoLを実行しない
    countdown = GRACETIME
    while countdown >= 0:
        # 10秒間LEDを点滅させながら待機
        led.on()
        utime.sleep(5)
        led.off()
        utime.sleep(5)
        countdown -= 10

    # ループの最後でクラスを開放し、ループ先頭に戻る
    print ('Shutdown complete. Restart loop.')
    del pad
