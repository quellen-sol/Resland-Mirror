#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/52c09e09a5310da912e4bc92cf183f9239d0aed6244441bc9d9499ca4153a796/contract';
import endContract from '../../snapshots/52c09e09a5310da912e4bc92cf183f9239d0aed6244441bc9d9499ca4153a796/contract.json' with { type: 'json' };
import type { Contract as Start } from '../../snapshots/be50cf86c51698349572a4290ed7a14af7374cfe98db45c480fd99b1d6e61037/contract';
import startContract from '../../snapshots/be50cf86c51698349572a4290ed7a14af7374cfe98db45c480fd99b1d6e61037/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col, fn, lit, primaryKey } from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'user_generated_resume',
        columns: [
          col('generated_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('s3_key', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('source_hash', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('template', 'text', {
            notNull: true,
            default: lit('original'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [primaryKey(['user_id'])],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_resume_format',
        columns: [
          col('captured_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('format', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('source_job_id', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [primaryKey(['user_id'])],
      }),
      this.addColumn({
        schema: 'public',
        table: 'user',
        column: col('summary', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.setDefault({
        schema: 'public',
        table: 'user',
        column: 'balance_cents',
        defaultSql: "DEFAULT '0'",
        operationClass: 'widening',
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_generated_resume',
        foreignKey: {
          name: 'user_generated_resume_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_resume_format',
        foreignKey: {
          name: 'user_resume_format_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
