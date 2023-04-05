# garage-manage

Raspberry Pi pico と距離センサー、リレーモジュールを組み合わせてガレージの諸々をIoT化する。

-距離センサーでシャッターの開度をチェック
-リレーで電動シャッターや照明、換気扇の操作

モノ側の制御実装はMicroPython

サービス側はFirebase上で、Firestore、Functions、Hosting、Authenticationなどを使用。
FunctionはTypescriptで実装。

アプリはIonic、Angularを使用。
PWAとして実装する。