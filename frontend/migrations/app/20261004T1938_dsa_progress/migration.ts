#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/4dbd015ad3e021f63ef04bfa31778f34a218409bd517c766541be7427453a580/contract';
import startContract from '../../snapshots/4dbd015ad3e021f63ef04bfa31778f34a218409bd517c766541be7427453a580/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/fbcfb6d73d6292fc83fe93d684ca06b76cc186f9582c456695cad477992ccb40/contract';
import endContract from '../../snapshots/fbcfb6d73d6292fc83fe93d684ca06b76cc186f9582c456695cad477992ccb40/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col, fn, primaryKey } from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'user_dsa_progress',
        columns: [
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('topic', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [primaryKey(['id'])],
      }),
      this.addUnique({
        schema: 'public',
        table: 'user_dsa_progress',
        constraint: 'user_dsa_progress_user_id_topic_key',
        columns: ['user_id', 'topic'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_dsa_progress',
        index: 'user_dsa_progress_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_dsa_progress',
        foreignKey: {
          name: 'user_dsa_progress_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
