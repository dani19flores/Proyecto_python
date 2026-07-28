-- Scripts SQL para crear las tablas de Hound Express (Guide, StatusHistory, User)
-- Generado con: python manage.py sqlmigrate shipments 0001

BEGIN;
--
-- Create model Estatus
--
CREATE TABLE "StatusHistory" ("id" integer NOT NULL PRIMARY KEY, "guideId" integer NOT NULL, "status" varchar(20) NOT NULL, "timestamp" datetime NOT NULL, "updatedBy" varchar(20) NOT NULL);
--
-- Create model Guia
--
CREATE TABLE "Guide" ("id" integer NOT NULL PRIMARY KEY, "trackingNumber" varchar(15) NOT NULL, "origin" varchar(100) NOT NULL, "destination" varchar(100) NOT NULL, "createdAt" date NOT NULL, "updatedAt" datetime NOT NULL, "currentStatus" varchar(20) NOT NULL);
--
-- Create model Usuario
--
CREATE TABLE "User" ("id" integer NOT NULL PRIMARY KEY, "name" varchar(50) NOT NULL, "email" varchar(50) NOT NULL, "password" varchar(20) NOT NULL, "createdAt" date NOT NULL, "updatedAt" datetime NOT NULL);
COMMIT;
