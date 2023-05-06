"""
Firebase操作
"""
import secrets
import urequests as requests
import ujson

IdToken = ""
RefreshToken = ""
ExpiresIn = 0

"""
認証処理
"""
def Authenticate():
    res = requests.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=' + secrets.FB_API_KEY,
                         headers = {'content-type': 'application/json'},
                         data = ujson.dumps({'email': secrets.FB_EMAIL, 'password': secrets.FB_PASSWORD, 'returnSecureToken': True}))
    print('RESULT code: {}'.format(res.status_code))
    if (res.status_code == 200):
        result = res.json()
        print(result)
        IdToken = result['idToken']
        RefreshToken = result['refreshToken']
        expiresIn = result['expiresIn']
        return True
    return False

"""
トークンリフレッシュ
"""
def RefreshToken():
    res = requests.post('https://securetoken.googleapis.com/v1/token?key=' + secrets.FB_API_KEY,
                         headers = {'content-type': 'application/x-www-form-urlencoded'},
                         data = 'grant_type=refresh_token&refresh_token=' + RefreshToken)
    if (res.status_code == 200):
        result = res.json()
        IdToken = result['id_token']
        RefreshToken = result['refresh_token']
        expiresIn = result['expires_in']
        return True
    return False

"""
Cloud Function 呼出し
"""
def CallFunction(funcName, data):
    res = requests.post('https://{0}-{1}.cloudfunctions.net/{2}'.format(secrets.FB_LOCATION, secrets.FB_PROJECT_ID, funcName),
     z                   headers = {'content-type': 'application/json', 'Authorization': 'Bearer {}'.format(IdToken) },
                        data = ujson.dumps({'data': data }))
    if (res.status_code == 200):
        return res.json()
    return None


