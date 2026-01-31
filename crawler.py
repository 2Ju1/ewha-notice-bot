import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re


class EwhaNoticeCrawler:
    def __init__(self):
        self.base_url = 'http://www.ewha.ac.kr'
        self.notice_url = '/ewha/news/notice.do'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/98.0.4758.102"
        }
    
    def crawl_notices(self, max_pages=2):
        """최근 공지사항 크롤링"""
        all_notices = []
        
        print(f"📥 이화여대 공지사항 크롤링 중...")
        
        for page in range(1, max_pages + 1):
            try:
                # 페이지 URL 생성
                if page == 1:
                    url = f"{self.base_url}{self.notice_url}"
                else:
                    url = f"{self.base_url}{self.notice_url}?artclList={page}"
                
                print(f"   페이지 {page} 요청: {url}")
                
                # 웹 페이지 요청
                req = requests.get(url, headers=self.headers, timeout=10)
                req.raise_for_status()
                html_content = req.text
                
                # BeautifulSoup 객체 생성
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 제목 박스 찾기 (b-title-box 클래스)
                title_boxes = soup.find_all(attrs={'class': 'b-title-box'})
                
                if not title_boxes:
                    print(f"   ⚠️ 페이지 {page}: 제목 박스를 찾을 수 없음")
                    # 대안: 테이블 행으로 찾기
                    notice_table = soup.select_one('table.board-table')
                    if notice_table:
                        notice_rows = notice_table.select('tbody tr')
                    else:
                        break
                else:
                    # b-title-box가 있는 행들 찾기
                    notice_rows = [box.find_parent('tr') for box in title_boxes if box.find_parent('tr')]
                
                if not notice_rows:
                    print(f"   ⚠️ 페이지 {page}: 공지를 찾을 수 없음")
                    break
                
                for row in notice_rows:
                    try:
                        tds = row.select('td')
                        if len(tds) < 5:
                            continue
                        
                        # 1. 번호 (공지/일반)
                        num_td = tds[0]
                        num_text = num_td.get_text(strip=True)
                        is_important = '공지' in num_text
                        
                        # 2. 구분 (학사/장학/입학/등록금/일반)
                        category_td = tds[1]
                        category = category_td.get_text(strip=True)
                        
                        # 3. 제목과 링크 (b-title-box 안에 있음)
                        title_box = tds[2].find(attrs={'class': 'b-title-box'})
                        if not title_box:
                            # 대안: a 태그 찾기
                            title_box = tds[2].find('a')
                        
                        if not title_box:
                            continue
                        
                        # 제목 추출
                        title = title_box.get_text(strip=True)
                        # 'N' 제거
                        title = title.replace(' N', '').replace('N ', '').strip()
                        
                        # 링크 추출 - onclick 이벤트 우선 확인
                        link_elem = title_box if title_box.name == 'a' else title_box.find('a')
                        if not link_elem:
                            link_elem = tds[2].find('a')
                        
                        link = ''
                        if link_elem:
                            # onclick 이벤트에서 goView() 함수의 파라미터 추출
                            onclick = link_elem.get('onclick', '')
                            if onclick and 'goView' in onclick:
                                # goView('?mode=view&articleNo=360336&article.offset=0&articleLimit=10') 형식
                                match = re.search(r"goView\('([^']+)'\)", onclick)
                                if match:
                                    link = match.group(1)
                            
                            # onclick이 없으면 href 사용
                            if not link:
                                link = link_elem.get('href', '')
                        
                        # URL 완성
                        if link:
                            if link.startswith('?'):
                                # ?mode=view&articleNo=... 형식 → notice.do 뒤에 붙이기
                                full_link = f"{self.base_url}/ewha/news/notice.do{link}"
                            elif link.startswith('/'):
                                full_link = f"{self.base_url}{link}"
                            elif link.startswith('http'):
                                full_link = link
                            else:
                                full_link = f"{self.base_url}/ewha/news/{link}"
                            
                            # URL 정리 (공백 제거)
                            full_link = full_link.replace(' ', '')
                        else:
                            full_link = ''
                        
                        # 4. 조회수
                        views_td = tds[3]
                        views = views_td.get_text(strip=True)
                        
                        # 5. 날짜
                        date_td = tds[4]
                        date_text = date_td.get_text(strip=True)
                        # YYYY.MM.DD 형식 추출
                        date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', date_text)
                        date = date_match.group(1) if date_match else date_text
                        
                        # 고유 ID 생성
                        notice_id = f"{title}_{date}".replace(' ', '_').replace('/', '_').replace('.', '_').replace('[', '').replace(']', '')
                        
                        all_notices.append({
                            'id': notice_id,
                            'category': category if category else '일반',
                            'title': title,
                            'link': full_link,
                            'date': date,
                            'views': views,
                            'is_important': is_important,
                            'crawled_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        print(f"⚠️ 공지 파싱 오류: {e}")
                        continue
                
                print(f"   페이지 {page}: {len(notice_rows)}개 처리 완료")
                time.sleep(1)  # 서버 부담 줄이기
                
            except requests.exceptions.HTTPError as e:
                print(f"⚠️ 페이지 {page} HTTP 오류: {e}")
                break
            except Exception as e:
                print(f"⚠️ 페이지 {page} 크롤링 실패: {e}")
                import traceback
                traceback.print_exc()
                break
        
        # 중복 제거
        seen_ids = set()
        unique_notices = []
        for notice in all_notices:
            if notice['id'] not in seen_ids:
                seen_ids.add(notice['id'])
                unique_notices.append(notice)
        
        print(f"✅ 총 {len(unique_notices)}개 공지 수집 완료")
        return unique_notices
    
    def get_new_notices(self, seen_file='seen_notices.json'):
        """새로운 공지만 필터링"""
        import json
        import os
        
        # 기존에 본 공지 로드
        if os.path.exists(seen_file):
            with open(seen_file, 'r', encoding='utf-8') as f:
                try:
                    seen_ids = set(json.load(f))
                except:
                    seen_ids = set()
        else:
            seen_ids = set()
        
        # 최신 공지 크롤링
        all_notices = self.crawl_notices()
        
        # 새 공지만 필터
        new_notices = [n for n in all_notices if n['id'] not in seen_ids]
        
        # seen 목록 업데이트 (최근 1000개만 유지)
        updated_seen = list(seen_ids | {n['id'] for n in all_notices})
        if len(updated_seen) > 1000:
            updated_seen = updated_seen[-1000:]
        
        with open(seen_file, 'w', encoding='utf-8') as f:
            json.dump(updated_seen, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 새 공지 {len(new_notices)}개 발견")
        return new_notices


# 테스트용 코드
if __name__ == "__main__":
    crawler = EwhaNoticeCrawler()
    
    # 전체 공지 크롤링 테스트
    print("=== 전체 공지 크롤링 테스트 ===")
    all_notices = crawler.crawl_notices(max_pages=1)
    
    print(f"\n📋 수집된 공지 {len(all_notices)}개:")
    for i, notice in enumerate(all_notices[:5], 1):
        print(f"\n{i}. [{notice['category']}] {notice['title']}")
        print(f"   날짜: {notice['date']} | 조회수: {notice['views']} | 중요: {'⭐ 공지' if notice['is_important'] else '일반'}")
        print(f"   링크: {notice['link']}")
    
    # 새 공지만 필터링 테스트
    print("\n\n=== 새 공지 필터링 테스트 ===")
    new_notices = crawler.get_new_notices()
    print(f"\n새로운 공지 {len(new_notices)}개 발견")
