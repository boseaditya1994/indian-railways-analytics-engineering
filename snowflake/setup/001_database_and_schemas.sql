-- Run only after reviewing account-level privileges and cost settings.
create database if not exists RAIL_DELAY_ANALYTICS;
create schema if not exists RAIL_DELAY_ANALYTICS.RAW;
create schema if not exists RAIL_DELAY_ANALYTICS.STAGING;
create schema if not exists RAIL_DELAY_ANALYTICS.INTERMEDIATE;
create schema if not exists RAIL_DELAY_ANALYTICS.MARTS;
create schema if not exists RAIL_DELAY_ANALYTICS.FEATURES;
create schema if not exists RAIL_DELAY_ANALYTICS.ML;
create schema if not exists RAIL_DELAY_ANALYTICS.AUDIT;

-- This project intentionally uses an existing account-managed warehouse (COMPUTE_WH by
-- default). Do not create or alter a warehouse here: size, suspend settings, and cost
-- policy remain governed by the account owner.
