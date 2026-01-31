# test.py - 각 단계별로 테스트

import os
os.environ['TELEGRAM_BOT_TOKEN'] = 'YOUR_TOKEN_HERE'
os.environ['TELEGRAM_CHAT_ID'] = 'YOUR_CHAT_ID_HERE'

def test_crawler():
    """크롤러 테스트"""
    print("=== 크롤러 테스트 ===")
    from crawler import EwhaNoticeCrawler
    
    crawler = EwhaNoticeCrawler()
    notices = crawler.crawl_notices(max_pages=1)
    
    print(f"✅ {len(notices)}개 공지 수집")
    if notices:
        print(f"예시: {notices[0]}")
    return notices

def test_ml(notices):
    """ML 모델 테스트"""
    print("\n=== ML 모델 테스트 ===")
    from model_predictor import NoticeClassifier
    

    classifier = NoticeClassifier('models/kobert_llrd.pth')
    titles = [n['title'] for n in notices[:5]]
    predictions = classifier.predict(titles)
    
    print("제목 -> 예측 결과:")
    for title, pred in zip(titles, predictions):
        label = "✅ 중요" if pred == 1 else "❌ 불필요"
        print(f"  {label}: {title}")

def test_telegram():
    """텔레그램 테스트"""
    print("\n=== 텔레그램 테스트 ===")
    from telegram_bot import TelegramBot
    
    bot = TelegramBot(
        os.getenv('TELEGRAM_BOT_TOKEN'),
        os.getenv('TELEGRAM_CHAT_ID')
    )
    
    test_notices = [{
        'category': '테스트',
        'title': '이화여대 공지 알림봇 테스트',
        'link': 'https://www.ewha.ac.kr',
        'date': '2024-01-30',
        'writer': '시스템',
        'is_important': True
    }]
    
    bot.send_notices(test_notices)
    print("✅ 텔레그램 전송 완료")

if __name__ == "__main__":
    # 1. 크롤러 테스트
    notices = test_crawler()
    
    # 2. ML 테스트
    if notices:
        test_ml(notices)
    
    # 3. 텔레그램 테스트
    test_telegram()
