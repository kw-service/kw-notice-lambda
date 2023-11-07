# KW 알리미 서버리스 백엔드

### kw-notice-api

MySQL 기반 데이터베이스에 접근하여 `python`을 이용해 공지사항 목록 조회하고 수정합니다.

### kw-notice-crawling

AWS Lambda에 올라가는 코드로써, 주기적으로 광운대학교 공지사항 목록을 크롤링하여 DB에 업데이트 합니다.
