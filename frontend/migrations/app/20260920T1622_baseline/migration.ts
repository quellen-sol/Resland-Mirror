#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/2ebc10a638e3daa23818a89dda5ef8edbc44a3a68f2cdcfb1ee01d700cf1c472/contract';
import endContract from '../../snapshots/2ebc10a638e3daa23818a89dda5ef8edbc44a3a68f2cdcfb1ee01d700cf1c472/contract.json' with { type: 'json' };
import {
  Migration,
  MigrationCLI,
  checkExpression,
  col,
  fn,
  lit,
  primaryKey,
} from '@prisma/orm-postgres/migration';

export default class M extends Migration<never, End> {
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createSchema({ schema: 'public' }),
      this.createTable({
        schema: 'public',
        table: 'user',
        columns: [
          col('auth0_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('email', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('full_name', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('has_onboarded', 'bool', {
            notNull: true,
            default: lit(false),
            codecRef: { codecId: 'pg/bool@1' },
          }),
          col('location', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('phone', 'text', { codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [primaryKey(['auth0_id'])],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_base_education',
        columns: [
          col('degree', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('description', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('end_date', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('field_of_study', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('institution', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('start_date', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [primaryKey(['id'])],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_base_experience',
        columns: [
          col('company_name', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('description', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('end_date', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('start_date', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('title', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [primaryKey(['id'])],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_base_experience_bullet',
        columns: [
          col('bullet', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('user_experience_id', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
        ],
        constraints: [primaryKey(['id'])],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_base_project',
        columns: [
          col('description', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('end_date', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('link', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('name', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('start_date', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [primaryKey(['id'])],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_base_skill',
        columns: [
          col('category', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('name', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [primaryKey(['id'])],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_social_link',
        columns: [
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('link', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('type', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'user_social_link_type_check_91780aba',
            "\"type\" IN ('LINKEDIN', 'GITHUB', 'WEBSITE')",
          ),
        ],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_suggestion',
        columns: [
          col('bullet_id', 'int4', { codecRef: { codecId: 'pg/int4@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('experience_id', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('pending_question', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('result', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('status', 'text', {
            notNull: true,
            default: lit('PROCESSING'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'user_suggestion_status_check_8152fec2',
            "\"status\" IN ('PROCESSING', 'WAITING_FOR_INPUT', 'COMPLETED')",
          ),
        ],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_upload_job',
        columns: [
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('s3_key', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('status', 'text', {
            notNull: true,
            default: lit('PENDING'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'user_upload_job_status_check_48358bb5',
            "\"status\" IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')",
          ),
        ],
      }),
      this.addUnique({
        schema: 'public',
        table: 'user_base_education',
        constraint: 'user_base_education_user_id_institution_degree_field_of_study_start_date_key',
        columns: ['user_id', 'institution', 'degree', 'field_of_study', 'start_date'],
      }),
      this.addUnique({
        schema: 'public',
        table: 'user_base_project',
        constraint: 'user_base_project_user_id_name_start_date_key',
        columns: ['user_id', 'name', 'start_date'],
      }),
      this.addUnique({
        schema: 'public',
        table: 'user_base_project',
        constraint: 'user_base_project_user_id_link_key',
        columns: ['user_id', 'link'],
      }),
      this.addUnique({
        schema: 'public',
        table: 'user_base_skill',
        constraint: 'user_base_skill_user_id_name_key',
        columns: ['user_id', 'name'],
      }),
      this.addUnique({
        schema: 'public',
        table: 'user_social_link',
        constraint: 'user_social_link_user_id_type_key',
        columns: ['user_id', 'type'],
      }),
      this.addUnique({
        schema: 'public',
        table: 'user_suggestion',
        constraint: 'user_suggestion_user_id_experience_id_bullet_id_key',
        columns: ['user_id', 'experience_id', 'bullet_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user',
        index: 'user_auth0_id_idx_0e027ea8',
        columns: ['auth0_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_base_education',
        index: 'user_base_education_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_base_experience',
        index: 'user_base_experience_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_base_experience_bullet',
        index: 'user_base_experience_bullet_user_experience_id_idx_b5f82fb4',
        columns: ['user_experience_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_base_project',
        index: 'user_base_project_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_base_skill',
        index: 'user_base_skill_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_social_link',
        index: 'user_social_link_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_suggestion',
        index: 'user_suggestion_bullet_id_idx_829f89ed',
        columns: ['bullet_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_suggestion',
        index: 'user_suggestion_experience_id_idx_9b808d03',
        columns: ['experience_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_suggestion',
        index: 'user_suggestion_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_upload_job',
        index: 'user_upload_job_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_base_education',
        foreignKey: {
          name: 'user_base_education_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_base_experience',
        foreignKey: {
          name: 'user_base_experience_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_base_experience_bullet',
        foreignKey: {
          name: 'user_base_experience_bullet_user_experience_id_fkey',
          columns: ['user_experience_id'],
          references: { schema: 'public', table: 'user_base_experience', columns: ['id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_base_project',
        foreignKey: {
          name: 'user_base_project_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_base_skill',
        foreignKey: {
          name: 'user_base_skill_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_social_link',
        foreignKey: {
          name: 'user_social_link_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_suggestion',
        foreignKey: {
          name: 'user_suggestion_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_suggestion',
        foreignKey: {
          name: 'user_suggestion_experience_id_fkey',
          columns: ['experience_id'],
          references: { schema: 'public', table: 'user_base_experience', columns: ['id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_suggestion',
        foreignKey: {
          name: 'user_suggestion_bullet_id_fkey',
          columns: ['bullet_id'],
          references: { schema: 'public', table: 'user_base_experience_bullet', columns: ['id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_upload_job',
        foreignKey: {
          name: 'user_upload_job_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
