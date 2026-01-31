import os
import requests


class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 환경변수가 설정되지 않았습니다.")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    
    def send_message(self, message):
        """텔레그램 메시지 전송"""
        # 메시지 길이 제한 (4096자)
        if len(message) > 4000:
            message = message[:4000] + "\n\n... (메시지가 너무 길어 생략됨)"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"✅ 메시지 전송 성공")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"❌ 메시지 전송 실패: {e}")
            print(f"   응답 내용: {response.text}")
            return False
        except Exception as e:
            print(f"❌ 메시지 전송 오류: {e}")
            return False
    
    def send_notices(self, notices):
        """공지사항 목록을 텔레그램으로 전송"""
        if not notices:
            print("📭 전송할 공지가 없습니다.")
            return
        
        # 메시지 생성
        message = "🔔 <b>이화여대 새 공지사항</b>\n\n"
        
        for i, notice in enumerate(notices, 1):
            category = notice.get('category', '일반')
            title = notice.get('title', '제목 없음')
            date = notice.get('date', '')
            link = notice.get('link', '')
            
            # HTML 특수문자 이스케이프
            title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            notice_msg = f"{i}. [{category}] {title}\n"
            notice_msg += f"   📅 {date}\n"
            notice_msg += f"   🔗 {link}\n\n"
            
            # 메시지가 너무 길어지면 분할 전송
            if len(message + notice_msg) > 4000:
                self.send_message(message)
                message = "🔔 <b>이화여대 새 공지사항 (계속)</b>\n\n" + notice_msg
            else:
                message += notice_msg
        
        # 마지막 메시지 전송
        self.send_message(message)
        print(f"✅ {len(notices)}개 공지 전송 완료")


# 테스트용 코드
if __name__ == "__main__":
    notifier = TelegramNotifier()
    
    test_notices = [
        {
            'category': '학사',
            'title': '테스트 공지사항입니다',
            'date': '2026.01.31',
            'link': 'https://www.ewha.ac.kr/test'
        }
    ]
    
    notifier.send_notices(test_notices)
