#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/11d5ad4d18483b4a5be49b098be34ab924ce9c6f0724186f14efc8c15d1afc62/contract';
import startContract from '../../snapshots/11d5ad4d18483b4a5be49b098be34ab924ce9c6f0724186f14efc8c15d1afc62/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/6a7a31751ea63f3115c80d946f1e6b42f2d43fdd73c84894c9900648ce6bfd95/contract';
import endContract from '../../snapshots/6a7a31751ea63f3115c80d946f1e6b42f2d43fdd73c84894c9900648ce6bfd95/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col, fn, lit, primaryKey } from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'site_settings',
        columns: [
          col('id', 'int4', { notNull: true, default: lit(1), codecRef: { codecId: 'pg/int4@1' } }),
          col('maintenance_mode', 'bool', {
            notNull: true,
            default: lit(false),
            codecRef: { codecId: 'pg/bool@1' },
          }),
          col('payments_paused', 'bool', {
            notNull: true,
            default: lit(false),
            codecRef: { codecId: 'pg/bool@1' },
          }),
          col('updated_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
        ],
        constraints: [primaryKey(['id'])],
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
