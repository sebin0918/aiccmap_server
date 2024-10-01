# AICC MAP PROJECT README 
1. Client = React
2. Server = Node.js
3. Client : 3000  /  Server : 5000  (front는 보통 3000 , node는 5000)

※ 주의 사항 ※
프롬프트 창을 두개를 열어서 각각 client와 server npm을 다르게 실행해줘야해요!

## 처음 실행전 database 작업

1. map_database 폴더로 이동
2. Mariadb 실행
3. 'data_to_exel.ipynb' 실행 - 데이터 생성
4. 'MAP_project_DATABASE.ipynb' 실행 - 데이터 적재

## front - client 시작 방법

1. cd (프로젝트의 client폴더 경로)
2. `npm install` 
3. `npm install recharts`
4. `npm install fullcalendar` 
5. `npm install @fullcalendar/react`
6. `npm install framer-motion`
7. `npm start`
// 필요시 아래까지 
7. react 환경설정 `.env` file.

## back - server 시작 방법 (node express)

1. cd (프로젝트의 server 폴더경로)
2. `npm install`
3. `npm install nodemailer`
4. `node join_security/hashExistingPasswords.js`
5. `npm install ioredis`
6. ctrl + c 
7. `node app.js`

## server 편리하게 사용하는  nodemon 사용방법
1. server 폴더 경로 이동
2. `npm install nodemon`
3. 사용 : `nodemon app.js`
(알아서 수정사항 반영해서 혼자 꺼졌다 켜짐)

## server - session 저장을 위한 redis 저장소 준비 
1) `wsl --install`
2) 사용할 username 설정 : `user`
3) 사용할 비밀번호 설정 : `user1234`
4) `sudo apt update`
5) `sudo apt install redis-server`
6) `sudo service redis-server start`
7) `.env` 파일 확인 

### wsl에서 현재 활성화된 session 확인방법
1) wsl 터미널 열기 
2) `redis-cli`
- `KEYS sess:*` → 세션 확인하기
- `FLUSHALL` → 강제로 현재 있는 세션들 삭제  

## DB 설정 변경 방법
1. server폴더의 `.env`
2. 프로젝트 db 세부설정 (자신의 db password로 변경)