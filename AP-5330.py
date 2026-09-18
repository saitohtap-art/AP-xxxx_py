# 区分機 サンプルプログラム
#
# このプログラムは python3 にて動作確認をしています。
# 使用に際しては、python3 の実行環境とあわせ、シリアル通信ライブラリを
# pip install pyserial にてインストールしてください。

######################################## シリアル通信設定
BAUDRATE = 38400
DATABITS = 8
PARITY = 'N'
STOPBITS = 1

######################################## コマンド設定
F_COMM = b'F'   #自動読取の場合は b'A'
RFID_FLAG = True    #RFID読み書き有無　不要な場合は False

######################################## 実行環境（シリアル通信）設定
import serial
from codecs import encode, decode

print('AP-5330用サンプルプログラムです。')
print('機器の通信設定は38400bps,8N1に設定してください。')
SERPORT = input("シリアルポート入力（COM?）:")

#シリアルポート設定（COMポート番号, ボーレート, データ長, パリティ, ストップビット, timeout, xonxoff, rtscts, dsrdtr）
ser = serial.Serial(SERPORT, BAUDRATE, DATABITS, PARITY, STOPBITS, 0.1)    #ポートオープン 
ser.rts=True  #制御線RTSオン
ser.dtr=True  #制御線DTRオン

######################################## 動作設定入力
START_POCKET = int(input("開始ポケット入力:"))
END_POCKET = int(input("終了ポケット入力:"))
ERR_POCKET = int(input("エラーポケット入力:"))

######################################## 関数定義
#RFIDステータス処理
def rfidStat(comm):
    ser.write(comm)  #コマンド送信
    data_rcv = b''  #受信データバッファ
    while True:
        data_rcv += ser.read_all()      #データ受信
        data_len = len(data_rcv) - 1    #データサイズ
        if data_len >= 2:   #データが3バイト以上確認
            if data_rcv[data_len] == ord('\r'):  #末尾CR受信確認
                data_txt = decode(data_rcv, 'shift_jis')    #シフトJISにてデコード
                print(data_txt)

                if data_rcv[0] == 0x1b:   #ESC
                    if data_rcv[1] == ord('C'):   # ESC C CR
                        print('RFID COM error')
                        ser.write(b'IF')
                        return b'C'
                    elif data_rcv[1] == ord('W'):   # ESC W CR
                        print('RFID Write error')
                        return b'W'
                    elif data_rcv[1] == ord('?'):   # ESC ? CR
                        print('RFID Read error')
                        return b'?'
                    elif data_rcv[1] == ord('0'):   # ESC 0 CR
                        print('RFID Write OK')
                        return b'0'
                    else:
                        #未対応ステータス
                        print('RFID STS error')
                        return b''
                else:
                    #読み取りOK
                    print('RFID Read OK')
                    return data_rcv[0:data_len]  #読み取りデータ

######################################## イニシャル処理
print('<処理開始>')
ser.write(b'I' + F_COMM)    #装置リセット＋読取送信

data_rcv = b''              #受信データバッファ
okPocket = START_POCKET     #OK時ポケット番号

######################################## メインループ処理
while True:
    data_rcv += ser.read_all()      #データ受信
    data_len = len(data_rcv) - 1    #データサイズ
    if data_len >= 2:   #データが3バイト以上確認
        if data_rcv[data_len - 2] == 0x1b and data_rcv[data_len] == ord('\r') and data_rcv[data_len - 1] != ord('?'):  #末尾ESC x CR受信確認 ?は除く
            data_txt = decode(data_rcv, 'shift_jis')    #シフトJISにてデコード
            print(data_txt)

            #ステータス確認 データ末尾で確認
            if data_rcv[data_len - 1] == ord('P'):     # ESC P CR
                print('POWER ON')
                ser.write(b'I' + F_COMM)
            elif data_rcv[data_len - 1] == ord('J'):   # ESC J CR
                print('JAM error')
                ser.write(b'IF')
            elif data_rcv[data_len - 1] == ord('D'):   # ESC D CR
                print('DBL error')
                ser.write(b'IF')
            elif data_rcv[data_len - 1] == ord('C'):   # ESC C CR
                print('COM error')
                ser.write(b'IF')
            elif data_rcv[data_len - 1] == ord('*'):   # ESC * CR
                print('SORTER error')
                ser.write(b'IF')
            elif data_rcv[data_len - 1] == ord('H'):   # ESC H CR
                print('HP empty')
                ser.write(b'IF')
            elif data_rcv[data_len - 1] == ord('E'):   # ESC E CR
                print('END')
                break    #終了
            elif data_rcv[data_len - 1] == ord('0'):   # ESC 0 CR
                if data_rcv[0] == 0x1b and data_rcv[1] == ord('?') and data_rcv[2] == ord('\r'):   # ESC ? CR
                    print('Read error')
                    pocketFlag = 0
                else:
                    print('Read OK')
                    readData_txt = decode(data_rcv[0:data_len - 3], 'shift_jis')  #読み取りデータ
                    pocketFlag = 1

                    #RFIDコマンド処理
                    if RFID_FLAG:
                        resultData = rfidStat(b'f0004\r')  #RFID読み取りコマンド
                        readData_txt = decode(resultData, 'shift_jis')  #読み取りデータ

                        if resultData == b'0' or len(resultData) > 1:  #正常応答または読み取りデータ確認
                            writeData = b'W00' + resultData + b'\r'  #RFID書き込みコマンド
                            resultData = rfidStat(writeData)

                        if resultData == b'C' or resultData == b'':
                            pocketFlag = -1
                        elif resultData == b'W' or resultData == b'?':
                            pocketFlag = 0

                #ポケット指定コマンド処理
                if pocketFlag >= 0:
                    if pocketFlag == 0:
                        pocketNum = ERR_POCKET
                    else:
                        pocketNum = okPocket

                        #OK時ポケットカウントアップ
                        okPocket += 1
                        if okPocket > END_POCKET:
                            okPocket = START_POCKET

                    #コマンド生成
                    if pocketNum < 100:
                        comm = 'S' + str(pocketNum).zfill(2)
                    else:
                        comm = 'S' + chr(pocketNum // 10 + 55) + str(pocketNum % 10)  #100～ ⇒ A0～

                    ser.write(comm.encode('ascii') + b'F')  #ポケット指定送信

            else:
                #未対応ステータス
                print('STS error')

            data_rcv = b''    #受信データクリア

######################################## エンド処理
ser.close()    #ポートクローズ
print('<処理終了>')
