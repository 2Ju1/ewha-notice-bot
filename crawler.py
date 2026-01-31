import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time


class EwhaNoticeCrawler:
    def __init__(self):
        self.base_url = 'https://www.ewha.ac.kr'
        self.notice_urls = {
            '전체공지': '/ewha/news/notice.do',
            '학사공지': '/ewha/news/notice.do?mode=list&srCategoryId=1',
            '장학공지': '/ewha/news/notice.do?mode=list&srCategoryId=2',
            '입학공지': '/ewha/news/notice.do?mode=list&srCategoryId=3',
            '등록금공지': '/ewha/news/notice.do?mode=list&srCategoryId=4',
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def crawl_notices(self, max_pages=2):
        """최근 공지사항 크롤링"""
        all_notices = []
        
        for category, url_path in self.notice_urls.items():
            print(f"📥 {category} 크롤링 중...")
            
            for page in range(1, max_pages + 1):
                try:
                    url = f"{self.base_url}{url_path}"
                    if '?' in url:
                        url += f"&srSearchKey=&srSearchVal=&page={page}"
                    else:
                        url += f"?page={page}"
                    
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    response.encoding = 'utf-8'
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 공지사항 테이블 찾기 (실제 사이트 구조에 맞춤)
                    notice_table = soup.select_one('table.board-table')
                    if not notice_table:
                        notice_table = soup.select_one('.board-list')
                    
                    if not notice_table:
                        print(f"   ⚠️ {category} 페이지 {page}: 테이블을 찾을 수 없음")
                        continue
                    
                    notice_rows = notice_table.select('tbody tr')
                    
                    for row in notice_rows:
                        try:
                            # 번호 (공지/일반 구분)
                            num_elem = row.select_one('td:first-child')
                            is_important = num_elem and '공지' in num_elem.get_text(strip=True)
                            
                            # 구분 (학사/장학/입학/등록금/일반)
                            category_elem = row.select('td')[1] if len(row.select('td')) > 1 else None
                            sub_category = category_elem.get_text(strip=True) if category_elem else ''
                            
                            # 제목과 링크
                            title_elem = row.select_one('td a')
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            # 'N' 마크 제거
                            title = title.replace(' N', '').replace('N ', '').strip()
                            
                            link = title_elem.get('href', '')
                            
                            # 전체 URL 생성
                            if link.startswith('http'):
                                full_link = link
                            elif link.startswith('/'):
                                full_link = f"{self.base_url}{link}"
                            else:
                                full_link = f"{self.base_url}/ewha/news/{link}"
                            
                            # 조회수와 날짜가 함께 있는 td
                            td_elements = row.select('td')
                            
                            # 날짜 추출 (마지막에서 두 번째 또는 마지막 td)
                            date = ''
                            for td in reversed(td_elements):
                                td_text = td.get_text(strip=True)
                                if '2026' in td_text or '2025' in td_text:
                                    # "조회수 xxx YYYY.MM.DD" 형식에서 날짜만 추출
                                    parts = td_text.split()
                                    for part in parts:
                                        if '.' in part and len(part) >= 8:
                                            date = part
                                            break
                                    if date:
                                        break
                            
                            # 고유 ID (제목 + 날짜로 중복 방지)
                            notice_id = f"{title}_{date}".replace(' ', '_').replace('/', '_')
                            
                            all_notices.append({
                                'id': notice_id,
                                'category': f"{category}>{sub_category}" if sub_category else category,
                                'title': title,
                                'link': full_link,
                                'date': date,
                                'is_important': is_important,
                                'crawled_at': datetime.now().isoformat()
                            })
                            
                        except Exception as e:
                            print(f"⚠️ 공지 파싱 오류: {e}")
                            continue
                    
                    print(f"   페이지 {page}: {len(notice_rows)}개 발견")
                    time.sleep(0.5)  # 서버 부담 줄이기
                    
                except Exception as e:
                    print(f"⚠️ {category} 페이지 {page} 크롤링 실패: {e}")
                    continue
        
        # 중복 제거 (같은 공지가 여러 카테고리에 나올 수 있음)
        seen_ids = set()
        unique_notices = []
        for notice in all_notices:
            if notice['id'] not in seen_ids:
                seen_ids.add(notice['id'])
                unique_notices.append(notice)
        
        print(f"✅ 총 {len(unique_notices)}개 공지 수집 완료 (중복 제거)")
        return unique_notices
    
    def get_new_notices(self, seen_file='seen_notices.json'):
        """새로운 공지만 필터링"""
        import json
        import os
        
        # 기존에 본 공지 로드
        if os.path.exists(seen_file):
            with open(seen_file, 'r', encoding='utf-8') as f:
                seen_ids = set(json.load(f))
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
        
        print(f"✅ 전체 {len(all_notices)}개 중 새 공지 {len(new_notices)}개 발견")
        return new_notices


# 테스트용 코드
if __name__ == "__main__":
    crawler = EwhaNoticeCrawler()
    notices = crawler.get_new_notices()
    
    print(f"\n📋 새 공지 {len(notices)}개:")
    for notice in notices[:10]:  # 최근 10개만 출력
        print(f"  - [{notice['category']}] {notice['title']}")
        print(f"    {notice['date']} | {notice['link']}")
