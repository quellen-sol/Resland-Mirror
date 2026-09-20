#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/4cfa9de85dda60dd8eabf3b7d38fdfb73de17bf860102235b1e9c846e345aa23/contract';
import endContract from '../../snapshots/4cfa9de85dda60dd8eabf3b7d38fdfb73de17bf860102235b1e9c846e345aa23/contract.json' with { type: 'json' };
import type { Contract as Start } from '../../snapshots/c922ffdeabd27a01d3cd2f3cabddfef92dd43eaf63acabacad4c2f2df8d84ecb/contract';
import startContract from '../../snapshots/c922ffdeabd27a01d3cd2f3cabddfef92dd43eaf63acabacad4c2f2df8d84ecb/contract.json' with { type: 'json' };
import {
  Migration,
  MigrationCLI,
  checkExpression,
  col,
  fn,
  lit,
  primaryKey,
} from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'user_tailor_run',
        columns: [
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('job_description', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
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
            'user_tailor_run_status_check_fa868dec',
            "\"status\" IN ('PROCESSING', 'WAITING_FOR_INPUT', 'COMPLETED', 'FAILED')",
          ),
        ],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_tailor_run',
        index: 'user_tailor_run_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_tailor_run',
        foreignKey: {
          name: 'user_tailor_run_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
