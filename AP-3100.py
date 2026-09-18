# リーダ機 サンプルプログラム
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
I_COMM = b'I\r'
F_COMM = b'F\r'
POK_COMM = b'P00\r'
PNG_COMM = b'P01\r'
RFID_FLAG = True    #RFID読み書き有無　不要な場合は False

######################################## 実行環境（シリアル通信）設定
import serial
from codecs import encode, decode

print('AP-3100用サンプルプログラムです。')
print('機器の通信設定は38400bps,8N1に設定してください。')
SERPORT = input("シリアルポート入力（COM?）:")

#シリアルポート設定（COMポート番号, ボーレート, データ長, パリティ, ストップビット, timeout, xonxoff, rtscts, dsrdtr）
ser = serial.Serial(SERPORT, BAUDRATE, DATABITS, PARITY, STOPBITS, 0.1)    #ポートオープン 
ser.rts=True  #制御線RTSオン
ser.dtr=True  #制御線DTRオン

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
ser.write(I_COMM)   #装置リセット送信

data_rcv = b''   #受信データバッファ

######################################## メインループ処理
while True:
    data_rcv += ser.read_all()      #データ受信
    data_len = len(data_rcv) - 1    #データサイズ
    if data_len >= 0:
        if data_rcv[data_len] == ord('\r'):  #末尾 CR 確認
            data_txt = decode(data_rcv, 'shift_jis')    #シフトJISにてデコード
            print(data_txt)

            #機器の電源投入直後の不要データ回避
            if data_len >= 3:
                if data_rcv[data_len - 2] == 0x1b and data_rcv[data_len - 1] == ord('P'):   #データ末尾 ESC P CR
                    data_rcv = b'\x1bP\r'   #ESC P CRへ書き換え

            #ステータス確認
            if data_len >= 2 and data_rcv[0] == 0x1b:   # ESC
                if data_rcv[1] == ord('P'):     # ESC P CR
                    print('POWER ON')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('C'):   # ESC C CR
                    print('COM error')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('J'):   # ESC J CR
                    print('JAM error')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('D'):   # ESC D CR
                    print('DBL error')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('H'):   # ESC H CR
                    print('HP empty')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('E'):   # ESC E CR
                    print('END')
                    break    #終了
                elif data_rcv[1] == ord('?'):   # ESC ? CR
                    print('Read error')
                    ser.write(PNG_COMM)
                elif data_rcv[1] == ord('0'):   # ESC 0 CR
                    ser.write(F_COMM)
                else:
                    #未対応ステータス
                    print('STS error')

            else:
                # 読み取りデータ処理
                print('Read OK')
                readData_txt = decode(data_rcv[0:data_len], 'shift_jis')  #読み取りデータ
                comm = POK_COMM

                #RFIDコマンド処理
                if RFID_FLAG:
                    resultData = rfidStat(b'FR0004\r')  #RFID読み取りコマンド
                    readData_txt = decode(resultData, 'shift_jis')  #読み取りデータ

                    if resultData == b'0' or len(resultData) > 1:  #正常応答または読み取りデータ確認
                        writeData = b'W00' + resultData + b'\r'  #RFID書き込みコマンド
                        resultData = rfidStat(writeData)

                    if resultData == b'C' or resultData == b'':
                        comm = I_COMM
                    elif resultData == b'W' or resultData == b'?':
                        comm = PNG_COMM

                ser.write(comm)

            data_rcv = b''    #受信データクリア

######################################## エンド処理
ser.close()    #ポートクローズ
print('<処理終了>')
