from crawler import EwhaNoticeCrawler
from model_predictor import NoticeClassifier
from telegram_bot import TelegramNotifier  # TelegramBot → TelegramNotifier


def test_crawler():
    """크롤러 테스트"""
    print("=== 크롤러 테스트 ===")
    crawler = EwhaNoticeCrawler()
    notices = crawler.crawl_notices(max_pages=1)
    print(f"✅ {len(notices)}개 공지 수집")
    return notices


def test_ml(notices):
    """ML 모델 테스트"""
    if not notices:
        print("⚠️ 테스트할 공지가 없습니다.")
        return []
    
    print("\n=== ML 분류 테스트 ===")
    classifier = NoticeClassifier('models/kobert_llrd.pth')
    
    titles = [notice['title'] for notice in notices[:5]]  # 처음 5개만
    predictions = classifier.predict(titles)
    
    print("제목 -> 예측 결과:")
    for title, pred in zip(titles, predictions):
        status = "✅ 중요" if pred == 1 else "❌ 불필요"
        print(f"  {status}: {title}")
    
    important_notices = [n for n, p in zip(notices[:5], predictions) if p == 1]
    return important_notices


def test_telegram():
    """텔레그램 전송 테스트"""
    print("\n=== 텔레그램 테스트 ===")
    
    test_notices = [
        {
            'category': '학사',
            'title': '테스트: 2026-1학기 수강신청 안내',
            'date': '2026.01.31',
            'link': 'http://www.ewha.ac.kr/ewha/news/notice.do?mode=view&articleNo=12345'
        },
        {
            'category': '장학',
            'title': '테스트: 2026학년도 장학금 신청 안내',
            'date': '2026.01.31',
            'link': 'http://www.ewha.ac.kr/ewha/news/notice.do?mode=view&articleNo=12346'
        }
    ]
    
    try:
        notifier = TelegramNotifier()  # TelegramBot → TelegramNotifier
        notifier.send_notices(test_notices)
        print("✅ 텔레그램 전송 완료")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")


if __name__ == "__main__":
    # 전체 테스트
    notices = test_crawler()
    important = test_ml(notices)
    test_telegram()
