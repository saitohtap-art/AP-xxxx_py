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
I_COMM = b'IF'  #読取位置変更コマンド使用時 b'IL050'

######################################## 実行環境（シリアル通信）設定
import serial
from codecs import encode, decode

print('AP-1500用サンプルプログラムです。')
print('機器の通信設定は38400bps,8N1に設定してください。')
SERPORT = input("シリアルポート入力（COM?）:")

#シリアルポート設定（COMポート番号, ボーレート, データ長, パリティ, ストップビット, timeout, xonxoff, rtscts, dsrdtr）
ser = serial.Serial(SERPORT, BAUDRATE, DATABITS, PARITY, STOPBITS, 0.1)    #ポートオープン 
ser.rts=True  #制御線RTSオン
ser.dtr=True  #制御線DTRオン

######################################## イニシャル処理
print('<処理開始>')
ser.write(I_COMM)   #装置リセット送信

data_rcv = b''   #受信データバッファ

######################################## メインループ処理
while True:
    data_rcv += ser.read_all()      #データ受信
    data_len = len(data_rcv) - 1    #データサイズ
    if data_len >= 0:
        if data_rcv[data_len] == ord('\r'):  #受信データ最後 CR 確認
            data_txt = decode(data_rcv, 'shift_jis')    #シフトJISにてデコード
            print(data_txt)

            #機器の電源投入直後の不要データ回避
            if data_len >= 3:
                if data_rcv[data_len - 2] == 0x1b and data_rcv[data_len - 1] == ord('P'):   #データ末尾 ESC P CR
                    data_rcv = b'\x1bP\r'   # ESC P CRへ書き換え

            #ステータス確認
            if data_len >= 2 and data_rcv[0] == 0x1b:   #ESC
                if data_rcv[1] == ord('P'):     # ESC P CR
                    print('POWER ON')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('C'):   # ESC C CR
                    print('COM error')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('U'):   # ESC U CR
                    print('JAM error')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('D'):   # ESC D CR
                    print('DBL error')
                    ser.write(I_COMM)
                elif data_rcv[1] == ord('?'):   # ESC ? CR
                    print('Read error')
                    ser.write(b'R')
                elif data_rcv[1] == ord('0'):   # ESC 0 CR
                    ser.write(b'F')
                else:
                    #未対応ステータス
                    print('STS error')

            else:
                # 読み取りデータ処理
                print('Read OK')
                readData_txt = decode(data_rcv[0:data_len], 'shift_jis')  #読み取りデータ
                ser.write(b'F')

            data_rcv = b''    #受信データクリア

######################################## エンド処理
ser.close()    #ポートクローズ
print('<処理終了>')
