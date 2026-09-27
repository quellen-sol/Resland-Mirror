#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/31540dd849f6e9c286da91907829aea32ce114a05372af52009b69d742dd4a43/contract';
import startContract from '../../snapshots/31540dd849f6e9c286da91907829aea32ce114a05372af52009b69d742dd4a43/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/b6062d92a59f3e4f6c0cacae41abdc2922326552bbc5187a36332ea1ab65762f/contract';
import endContract from '../../snapshots/b6062d92a59f3e4f6c0cacae41abdc2922326552bbc5187a36332ea1ab65762f/contract.json' with { type: 'json' };
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
