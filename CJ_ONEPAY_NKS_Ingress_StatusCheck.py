import hashlib
import hmac
import base64
import requests
import time
import json

# Cloud Function 디폴트 파라미터
# {
#     "base_url":"https://fin-ncloud.apigw.fin-ntruss.com",
#     "api_url":"/vloadbalancer/v2/getLoadBalancerInstanceList?regionCode=FKR&responseFormatType=json",
#     "access_key":"Sub Account Access Key",
#     "secret_key":"Sub Account Secret Key",
#      "hookurl":"Slack Hook URL"
#     }


# Sub Account Secret Key 이용하여 NCP API 호출 위한 서명 생성 함수
def make_signature(url, timestamp, access_key, secret_key):
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)

    secret_key = bytes(secret_key, "UTF-8")

    method = "GET"

    message = method + " " + url + "\n" + timestamp + "\n" + access_key
    message = bytes(message, "UTF-8")
    sign_key = base64.b64encode(
        hmac.new(secret_key, message, digestmod=hashlib.sha256).digest()
    )
    print(sign_key)
    return sign_key

# NCP API 호출 위한 Header 값 생성 함수
def make_header(timestamp, access_key, sign_key):
    headers = {
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": access_key,
        "x-ncp-apigw-signature-v2": sign_key,
    }
    return headers

# Slack Notification 함수  
def post_slack(hookurl, text):
    hookurl = hookurl
    payload = { "text" : text}
    requests.post(hookurl, json=payload)

# Cloud Function Main 함수
def main(args):
    timestamp = str(int(time.time() * 1000))
    
    api_url_with_params = args["api_url"]
    url = f'{args["base_url"]}{api_url_with_params}'

    sign_key = make_signature(
        api_url_with_params, timestamp, args["access_key"], args["secret_key"]
    )
    headers = make_header(timestamp, args["access_key"], sign_key)
    # Cloud Function 함수 호출 성공 시 Return 값 위한 list 변수 설정
    api_return = []
    try:
        res = requests.get(url, headers=headers)
        result = json.loads(res.text)
        lb_list = result["getLoadBalancerInstanceListResponse"]["loadBalancerInstanceList"]
        
        
        for i in range(len(lb_list)):
            lb_status = lb_list[i]["loadBalancerInstanceStatusName"]
            lb_name = lb_list[i]["loadBalancerName"]
            if lb_status == "Running":
                post_slack(args["hookurl"], f'{lb_name} 은 정상')
                api_return.append(lb_name)
    except Exception as e:
        raise Exception({"done": False, "error_message": str(e)})
    return {"lb_name" : api_return}