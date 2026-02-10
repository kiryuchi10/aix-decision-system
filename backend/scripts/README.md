# Backend Scripts

## DB 설정

- **스키마 적용**: `backend/schema.sql`이 단일 DDL 소스입니다.
  - MySQL에 DB 생성 후: `mysql -u root -p your_db < ../schema.sql`
  - Windows: `Get-Content ..\schema.sql -Raw | mysql -u root -p your_db`
- **DB + 사용자 생성 (선택)**: `mysql_init_env.sql`로 DB·사용자 생성 후, 테이블은 위 `schema.sql`로 적용 권장.
- **PowerShell**: `run_schema.ps1`, `run_mysql_init_env.ps1` / **Windows**: `setup_database.bat`, `setup_database.ps1`

## 기타

- `create_default_user.py`, `import_seed_*.py`, `migrate_*.py`, `seed_*.py`: 사용자/시드/마이그레이션.
