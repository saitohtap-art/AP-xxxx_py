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

######################################## 実行環境（シリアル通信）設定
import serial
from codecs import encode, decode

print('AP-3270用サンプルプログラムです。')
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

######################################## イニシャル処理
print('<処理開始>')
ser.write(b'I' + F_COMM)    #装置リセット＋読取送信

data_rcv = b''              #受信データバッファ
okPocket = START_POCKET     #OK時ポケット番号

######################################## メインループ処理
while True:
    data_rcv += ser.read_all()      #データ受信
    data_len = len(data_rcv) - 1    #データサイズ
    if data_len >= 2:
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
                    pocketNum = ERR_POCKET
                else:
                    print('Read OK')
                    readData_txt = decode(data_rcv[0:data_len - 3], 'shift_jis')  #読み取りデータ
                    pocketNum = okPocket

                    #OK時ポケットカウントアップ
                    okPocket += 1
                    if okPocket > END_POCKET:
                        okPocket = START_POCKET

                ser.write(b'S' + str(pocketNum).zfill(2).encode('ascii') + b'F')  #ポケット指定送信

            else:
                #未対応ステータス
                print('STS error')

            data_rcv = b''    #受信データクリア

######################################## エンド処理
ser.close()    #ポートクローズ
print('<処理終了>')
