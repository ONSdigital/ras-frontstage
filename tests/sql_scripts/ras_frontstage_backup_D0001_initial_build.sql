--liquibase formatted sql
--changeset ras_frontstage_backup:R1_0_0.ras_frontstage_backup_D0001_initial_build.sql

-- R Ingram Initial build 09/03/2017

--
-- Schema: ras_frontstage_backup
--
DROP SCHEMA IF EXISTS ras_frontstage_backup CASCADE;
CREATE SCHEMA ras_frontstage_backup;

--
-- User: ras_frontstage_backup
--
DROP USER IF EXISTS ras_frontstage_backup;
CREATE USER ras_frontstage_backup WITH PASSWORD 'password'
  SUPERUSER INHERIT CREATEDB CREATEROLE NOREPLICATION;

--
-- Table: user [USE]
--
DROP TABLE IF EXISTS ras_frontstage_backup.user;

CREATE TABLE ras_frontstage_backup.users
(id                BIGSERIAL                NOT NULL
,username          CHARACTER VARYING (100)  NOT NULL
,pwdhash           TEXT                     NOT NULL
,token             TEXT
,token_created_on  TIMESTAMP WITH TIME ZONE
,token_duration    INTEGER
,created_on        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
,CONSTRAINT ras_use_pk
  PRIMARY KEY (id)
,CONSTRAINT ras_use_uk
  UNIQUE (username)
);

INSERT INTO ras_frontstage_backup.users
  (username,pwdhash)
VALUES
  ('nherriott@nowwhere.com','password')
 ,('cfreduah@nowwhere.com','password')
 ,('mprice@nowwhere.com','password')
 ,('ringram@nowwhere.com','password');

 --
 -- Table: user_scopes [USC]
 --
 CREATE TABLE ras_frontstage_backup.user_scopes
 (id            BIGSERIAL                NOT NULL
 ,user_id       INTEGER                  NOT NULL
 ,scope         CHARACTER VARYING (100)  NOT NULL
 ,created_on    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
 ,CONSTRAINT ras_uss_pk
   PRIMARY KEY (id)
 ,CONSTRAINT ras_uss_use_fk
   FOREIGN KEY (user_id)
     REFERENCES ras_frontstage_backup.users(id)
 );

 INSERT INTO ras_frontstage_backup.user_scopes
   (user_id,scope)
 VALUES
   ((SELECT id FROM ras_frontstage_backup.users WHERE username = 'nherriott@nowwhere.com'),'ci.read')
  ,((SELECT id FROM ras_frontstage_backup.users WHERE username = 'nherriott@nowwhere.com'),'ci.write')
  ,((SELECT id FROM ras_frontstage_backup.users WHERE username = 'cfreduah@nowwhere.com'),'ci.read')
  ,((SELECT id FROM ras_frontstage_backup.users WHERE username = 'cfreduah@nowwhere.com'),'ci.write')
  ,((SELECT id FROM ras_frontstage_backup.users WHERE username = 'mprice@nowwhere.com'),'ci.read')
  ,((SELECT id FROM ras_frontstage_backup.users WHERE username = 'ringram@nowwhere.com'),'ci.read');

 --
 -- Index: ras_cic_coi_fk_idx - FK Index
 --
 CREATE INDEX ras_uss_use_fk_idx ON ras_frontstage_backup.user_scopes (user_id);

COMMIT;

--rollback DROP TABLE ras_frontstage_backup.user;
