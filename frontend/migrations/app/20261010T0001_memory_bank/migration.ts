#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/2a58999b51b3503b8c6569732cb669bc995b8dc9956278b249faa686b3f7b57c/contract';
import startContract from '../../snapshots/2a58999b51b3503b8c6569732cb669bc995b8dc9956278b249faa686b3f7b57c/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/376e701151882455ac9a9290b31faefbaf5d512847d139694f39f2a9a7745c4f/contract';
import endContract from '../../snapshots/376e701151882455ac9a9290b31faefbaf5d512847d139694f39f2a9a7745c4f/contract.json' with { type: 'json' };
import {
  Migration,
  MigrationCLI,
  checkExpression,
  col,
  fn,
  primaryKey,
} from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'user_memory_fact',
        columns: [
          col('content', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('source', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('topic', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('updated_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'user_memory_fact_source_check_e8ce388e',
            "\"source\" IN ('TAILOR', 'SUGGESTION', 'USER')",
          ),
        ],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_memory_fact',
        index: 'user_memory_fact_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_memory_fact',
        foreignKey: {
          name: 'user_memory_fact_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
