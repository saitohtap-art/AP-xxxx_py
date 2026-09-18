# プリンタ サンプルプログラム
#
# このプログラムは python3 にて動作確認をしています。
# 使用に際しては、python3 の実行環境とあわせ、シリアル通信ライブラリを
# pip install pyserial にてインストールしてください。
import serial

print('AP-4360用サンプルプログラムです。')
print('プリンタをリードモードに設定し使用してください。')
print('機器の通信設定は38400bps,8N1に設定してください。')
SERPORT = input("シリアルポート入力（COM?）:")

######################################## シリアル通信設定
BAUDRATE = 38400
DATABITS = 8
PARITY = 'N'
STOPBITS = 1
XONXOFF = True
#シリアルポート設定（COMポート番号, ボーレート, データ長, パリティ, ストップビット, timeout, xonxoff, rtscts, dsrdtr）
ser = serial.Serial(SERPORT, BAUDRATE, DATABITS, PARITY, STOPBITS, 0.1, XONXOFF)    #ポートオープン 
ser.rts=True  #制御線RTSオン
ser.dtr=True  #制御線DTRオン

######################################## コマンド設定
# RFIDの00ブロックのデータをカウントアップして印刷します。
I_COMM = b'IF0008\r'
F_COMM = b'F0008\r'   #自動読取の場合は b'A'

ESC = b'\x1B'
LFNUL = b'\x0A\x00'
#印刷データ
PrintData = [ESC + b'D1505,0750,1500' + LFNUL]
PrintData += [ESC + b'C' + LFNUL]
PrintData += [ESC + b'LC;0050,0050,0700,0560,1,5' + LFNUL]
PrintData += [ESC + b'LC;0050,0220,0700,0220,0,3' + LFNUL]
PrintData += [ESC + b'LC;0050,0390,0700,0390,0,3' + LFNUL]
PrintData += [ESC + b'LC;0240,0050,0240,0560,0,3' + LFNUL]
PrintData += [ESC + b'PC00;0070,0160,1,1,X,00,B' + LFNUL]
PrintData += [ESC + b'PC01;0070,0330,15,2,V,00,B' + LFNUL]
PrintData += [ESC + b'PC02;0070,0490,1,1,X,00,B' + LFNUL]
PrintData += [ESC + b'PC03;0260,0200,2,4,W,00,B' + LFNUL]
PrintData += [ESC + b'PC04;0260,0540,3,5,W,00,B' + LFNUL]
PrintData += [ESC + b'PC05;0150,0740,2,1,A,00,B' + LFNUL]
PrintData += [ESC + b'PV01;0260,0370,0100,0150,B,00,B' + LFNUL]
PrintData += [ESC + b'XB00;0070,0590,3,1,03,03,09,09,03,0,0120' + LFNUL]
PrintData += [ESC + b'XB01;0300,0790,T,M,06,A,0,M2' + LFNUL]
PrintData += [ESC + b'RC00;' + 'メーカー'.encode('shift_jis') + LFNUL]
PrintData += [ESC + b'RC01;' + '業者コード'.encode('shift_jis') + LFNUL]
PrintData += [ESC + b'RC02;' + '製品名'.encode('shift_jis') + LFNUL]
PrintData += [ESC + b'RC03;' + 'APリファイン'.encode('shift_jis') + LFNUL]
PrintData += [ESC + b'RC04;' + 'AP-4360'.encode('shift_jis') + LFNUL]
PrintData += [ESC + b'RC05;1234567890ABC' + LFNUL]
PrintData += [ESC + b'RV01;915001' + LFNUL]
PrintData += [ESC + b'RB00;1234567890ABC' + LFNUL]
PrintData += [ESC + b'RB01;1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890' + LFNUL]
PrintData += [ESC + b'XS;I,0001,0000C3010' + LFNUL]
#白紙印刷データ
BlankData = [ESC + b'D1505,0750,1500' + LFNUL + ESC + b'C' + LFNUL + ESC + b'XS;I,0001,0000C3000' + LFNUL]

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
                data_txt = data_rcv.decode('shift_jis')    #シフトJISにてデコード
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
                    return data_rcv[0:data_len]  #読み取りデータを返す

#印刷処理 ※印刷データが9999バイト以上の場合は分割して送るようにしてください
def rewritePrint(dataList):
    ser.write(b'P0')
    for data in dataList:
        ser.write(str(len(data)).zfill(4).encode('ascii'))
        ser.write(data)
    ser.write(b'0000')

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
            data_txt = data_rcv.decode('shift_jis')    #シフトJISにてデコード
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
                    rewritePrint(BlankData)  #エラー印刷
                elif data_rcv[1] == ord('0'):   # ESC 0 CR
                    #正常印刷
                    ser.write(F_COMM)
                else:
                    #未対応ステータス
                    print('STS error')

            else:
                # 読み取りデータ処理
                print('Read OK')

                #RFID カウンタ値の読み取り
                resultData = rfidStat(b'F0001\r')  #RFID 00ブロック読み取り
                if len(resultData) >= 4:
                    try:
                        count = int(resultData)  #データ文字 ⇒ 数値
                    except ValueError:
                        count = 0
                    count += 1  #カウントアップ
                
                    #RFID カウンタ値の書き込み
                    resultData = rfidStat(b'W00' + str(count).zfill(4).encode('ascii') + b'\r')  #RFID 00ブロック書き込み
                    if resultData == b'0':
                        rewritePrint(PrintData)  #正常印刷

                if resultData == b'?' or resultData == b'W':
                    rewritePrint(BlankData)  #エラー印刷
                elif resultData == b'C' or resultData == b'':
                    ser.write(I_COMM)

            data_rcv = b''    #受信データクリア

######################################## エンド処理
ser.close()    #ポートクローズ
print('<処理終了>')
