import sys
from pyzbar.pyzbar import decode
from PIL import Image
import re
import urllib.parse

def decode_qr_code(image_path):
    """QR 코드 이미지에서 데이터 추출"""
    try:
        # 이미지 열기
        img = Image.open(image_path)
        
        # QR 코드 디코딩
        decoded_objects = decode(img)
        
        if not decoded_objects:
            print("QR 코드를 찾을 수 없습니다.")
            return None
            
        # 첫 번째 QR 코드 데이터 추출
        qr_data = decoded_objects[0].data.decode("utf-8")
        print(f"추출된 QR 코드 데이터: {qr_data}")
        
        # TOTP URL 형식 확인
        if qr_data.startswith("otpauth://"):
            # URL에서 secret 파라미터 추출
            match = re.search(r"secret=([A-Z0-9]+)", qr_data)
            if match:
                secret = match.group(1)
                print(f"추출된 비밀 키: {secret}")
                return secret
            else:
                print("비밀 키를 찾을 수 없습니다.")
                # URL 파싱 시도
                parsed_url = urllib.parse.urlparse(qr_data)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'secret' in query_params:
                    secret = query_params['secret'][0]
                    print(f"URL 파싱으로 추출된 비밀 키: {secret}")
                    return secret
        else:
            print("일반 텍스트 QR 코드입니다. 전체 내용:")
            print(qr_data)
            return qr_data
            
    except Exception as e:
        print(f"오류 발생: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python decode_qr.py <QR_코드_이미지_경로>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    decode_qr_code(image_path)