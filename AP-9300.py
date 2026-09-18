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
POK_COMM = b'P0\r'
PNG_COMM = b'P1\r'
W_COMM = b''  #RFID書込時に指定 b'W00abcd\r'、書込不要な場合はb''、都度データ入力する場合は書込開始ブロックのみ指定 b'W00'

######################################## 実行環境（シリアル通信）設定
import serial
from codecs import encode, decode

print('AP-9300用サンプルプログラムです。')
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
                elif data_rcv[1] == ord('U'):   # ESC U CR
                    print('JAM error')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('?'):   # ESC ? CR
                    print('Read error')
                    ser.write(PNG_COMM)
                elif data_rcv[1] == ord('0'):   # ESC 0 CR
                    ser.write(F_COMM)
                else:
                    #未対応ステータス
                    print('STS error')

            else:
                #読み取りデータ処理
                print('Read OK')

                #RFID書き込み処理
                if W_COMM != b'':
                    if len(W_COMM) > 3:
                        write_comm = W_COMM
                    else:
                        writeData = input("RFID書き込みデータ入力:")
                        data_sjis = encode(writeData, 'shift_jis')    #シフトJISにてエンコード
                        write_comm = W_COMM + data_sjis + b'\r'  #RFID書き込みコマンド
                    resultData = rfidStat(write_comm)
                    if resultData == b'0':
                        ser.write(POK_COMM)
                    elif resultData == b'W' or resultData == b'?':
                        ser.write(PNG_COMM)
                    else:
                        ser.write(I_COMM)
                else:
                    ser.write(POK_COMM)

            data_rcv = b''    #受信データクリア

######################################## エンド処理
ser.close()    #ポートクローズ
print('<処理終了>')
