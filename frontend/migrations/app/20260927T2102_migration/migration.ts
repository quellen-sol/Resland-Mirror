#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/bc3ed381debcbee76352fb5ba436fd0db987dc694f94fc7a46913c0dc559498e/contract';
import endContract from '../../snapshots/bc3ed381debcbee76352fb5ba436fd0db987dc694f94fc7a46913c0dc559498e/contract.json' with { type: 'json' };
import type { Contract as Start } from '../../snapshots/c9d11cbec8d8698eec9378f615f694ee856fcda93f97b0270c507997cef9ac8a/contract';
import startContract from '../../snapshots/c9d11cbec8d8698eec9378f615f694ee856fcda93f97b0270c507997cef9ac8a/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col, fn, primaryKey } from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'user_tailored_resume',
        columns: [
          col('company_name', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('content', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('generated_at', 'timestamptz', {
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('job_description', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('role', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('s3_key', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('source_hash', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('tailor_run_id', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('updated_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [primaryKey(['id'])],
      }),
      this.addColumn({
        schema: 'public',
        table: 'user_tailor_run',
        column: col('company_name', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.addColumn({
        schema: 'public',
        table: 'user_tailor_run',
        column: col('role', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.addUnique({
        schema: 'public',
        table: 'user_tailored_resume',
        constraint: 'user_tailored_resume_user_id_tailor_run_id_key',
        columns: ['user_id', 'tailor_run_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_tailored_resume',
        index: 'user_tailored_resume_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_tailored_resume',
        foreignKey: {
          name: 'user_tailored_resume_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
