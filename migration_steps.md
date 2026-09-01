## Step 1: Create a new database
```
CREATE DATABASE apiary_dev;
CREATE USER apiary_dev WITH PASSWORD '<password>';
GRANT ALL PRIVILEGES ON DATABASE "apiary_dev" to apiary_dev;
\c apiary_dev
create extension postgis;
GRANT ALL ON ALL TABLES IN SCHEMA public TO apiary_dev;
GRANT ALL ON SCHEMA public TO apiary_dev;
```

## Step 2: Dump data and reversion schema from the ledger_prod
```
pg_dump -U ledger_prod -W --exclude-table='django_cron*' -t 'disturbance_*' -t 'django_*' -t 'taggit_*' -t 'auth_group' -t 'auth_permission' -t 'accounts_document' ledger_prod -h <host> > /tmp/apiary_ledger_tables_YYYYMMDD.sql
pg_dump --schema-only -U ledger_prod -W -t 'reversion_*' -h <host> > /tmp/reversion_schema_apiary_ledger_tables.sql
```
Enter password for the ledger_prod database

## Step 3: Import dumped data and reversion schema into newly created database
```
psql -U apiary_dev apiary_dev -W -h <host> < /tmp/apiary_ledger_tables_YYYYMMDD.sql
psql -U apiary_dev apiary_dev -W -h <host> < /tmp/reversion_schema_apiary_ledger_tables.sql
```
Enter password for the apiary_dev database

## Step 4: Fix and Apply migrations
### 1. Create copy of table: django_migrations
```
CREATE TABLE django_migrations_temp AS SELECT * from django_migrations;
```
### 2. Delete migrations in order to apply ledger_api_client migrations
```
delete from django_migrations where id > 11;
```
### 3. Apply ledger_api_client migrations
```
python manage.py migrate ledger_api_client
```
### 4. Reinsert the migrations that were deleted in the Step 4-2
```
insert into django_migrations (id,app,name,applied) select * from  django_migrations_temp  where id > 11;
```
### 5. Apply other migrations
```
./manage.py migrate admin
./manage.py migrate disturbance
./manage.py migrate
```
## Step 5: Additional setup requirements (non database related)
### 1. Make sure the licence remplate .docx file exists
```
- Go into the django admin and navigate to the 'Global Settings' area.
- Find the key 'Apiary licence template file' 
- Either clear and reupload the template file (you can copy it from production using azcopy in the appsteam-tools sidecar)
- or simply move it into the expected file path of 'media/apiary_licence_template/apiary_authority_permit_template_v3_friI1ma.docx' (file name may be slightly different)
```