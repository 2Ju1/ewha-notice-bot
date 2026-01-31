# telegram_bot.py

import requests
from datetime import datetime

class TelegramBot:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text):
        """메시지 전송"""
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False  # 링크 미리보기 활성화
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ 메시지 전송 실패: {e}")
            return False
    
    def send_notices(self, notices):
        """공지사항들을 보기 좋게 포맷해서 전송"""
        if not notices:
            return
        
        # 헤더 메시지
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        header = f"🎓 <b>이화여대 새 공지</b> ({len(notices)}건)\n"
        header += f"⏰ {now}\n"
        header += "─" * 30 + "\n\n"
        
        # 카테고리별로 그룹화
        by_category = {}
        for notice in notices:
            cat = notice['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(notice)
        
        # 중요도 순 정렬 (중요 공지 먼저)
        for cat in by_category:
            by_category[cat].sort(key=lambda x: (not x.get('is_important', False), x['date']), reverse=True)
        
        # 카테고리별 메시지 생성
        messages = []
        current_message = header
        
        for category, items in by_category.items():
            cat_section = f"📌 <b>{category}</b> ({len(items)}건)\n\n"
            
            for i, notice in enumerate(items, 1):
                # 중요 공지 표시
                prefix = "⭐ " if notice.get('is_important') else f"{i}. "
                
                item_text = f"{prefix}<b>{notice['title']}</b>\n"
                item_text += f"   📅 {notice['date']}"
                if notice.get('writer'):
                    item_text += f" | {notice['writer']}"
                item_text += f"\n   🔗 <a href='{notice['link']}'>공지 보기</a>\n\n"
                
                # 메시지 길이 체크 (텔레그램 4096자 제한)
                if len(current_message + cat_section + item_text) > 3800:
                    messages.append(current_message)
                    current_message = cat_section + item_text
                else:
                    if cat_section not in current_message:
                        current_message += cat_section
                    current_message += item_text
        
        # 마지막 메시지 추가
        if current_message != header:
            messages.append(current_message)
        
        # 메시지 전송
        success_count = 0
        for msg in messages:
            if self.send_message(msg):
                success_count += 1
        
        print(f"✅ {success_count}/{len(messages)} 메시지 전송 완료")
        return success_count > 0


# 테스트용
if __name__ == "__main__":
    import os
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        bot = TelegramBot(token, chat_id)
        bot.send_message("✅ 텔레그램 봇 테스트 성공!")
    else:
        print("환경변수를 설정해주세요")