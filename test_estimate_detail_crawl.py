from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from login_and_crawl import login
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_NAME = '게임더하기_계약관리'  # 실제 구글 시트명으로 맞게 수정
WORKSHEET_NAME = '게임더하기_계약_2025'  # 실제 워크시트명으로 맞게 수정

def get_gsheet():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('google_service_account.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
    return sheet

def test_estimate_detail_crawl_and_update_sheet():
    driver = login()
    driver.get('https://gsp.kocca.kr/admin/serviceReq/serviceReqListPage.do')

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "dataList"))
    )

    rows = driver.find_elements(By.CSS_SELECTOR, "#dataList tbody tr")
    found = False
    for row in rows:
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 8:
            continue
        번호 = tds[0].text.strip()
        입찰마감일 = tds[6].text.strip()
        if 번호 == "1585" and 입찰마감일 == "2024-11-24":
            found = True
            try:
                # login_and_crawl.py와 동일하게 전체 row 추출
                row_data = [td.text.strip() for td in tds]
                estimate_link = tds[5].find_element(By.TAG_NAME, "a")
                estimate_link.click()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.division30 #dataList"))
                )
                time.sleep(1)
                detail_rows = driver.find_elements(By.CSS_SELECTOR, "div.division30 #dataList tbody tr")
                estimates = []
                for drow in detail_rows:
                    dtds = drow.find_elements(By.TAG_NAME, "td")
                    if len(dtds) < 7:
                        continue
                    협력사 = dtds[1].text.strip()
                    견적일자 = dtds[3].text.strip()
                    견적금액 = dtds[4].text.strip()
                    estimates.append(f"{협력사}({견적금액}, {견적일자})")
                driver.back()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "dataList"))
                )
                time.sleep(1)
                estimate_status = '\n'.join(estimates) if estimates else "없음"
                print(f"견적서 제출현황: \n{estimate_status}")

                # 구글 시트 업데이트 (전체 row 기준)
                sheet = get_gsheet()
                all_rows = sheet.get_all_values()
                header = all_rows[0]
                for idx, srow in enumerate(all_rows[1:], start=2):
                    if srow[0].strip() == 번호 and srow[6].strip() == 입찰마감일:
                        # header 기준으로 row_data 길이 맞추기
                        if '견적서제출현황' in header:
                            col_idx = header.index('견적서제출현황')
                            # row_data 길이 부족하면 빈 칸 채우기
                            if len(row_data) < len(header):
                                row_data += [''] * (len(header) - len(row_data))
                            row_data[col_idx] = estimate_status
                        else:
                            row_data.append(estimate_status)
                        # 전체 row를 업데이트
                        col_end = chr(65+len(row_data)-1)
                        sheet.update(f'A{idx}:{col_end}{idx}', [row_data])
                        print(f"구글 시트 {idx}행 전체 row를 견적서 제출현황 포함해 업데이트 완료!")
                        break
            except Exception as e:
                print(f"상세페이지 진입 또는 크롤링/시트 업데이트 실패: {e}")
            break
    if not found:
        print("테스트 대상 행(번호 1585, 입찰마감일 2024-11-24)을 찾을 수 없습니다.")
    driver.quit()

if __name__ == "__main__":
    test_estimate_detail_crawl_and_update_sheet() 