#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/2a58999b51b3503b8c6569732cb669bc995b8dc9956278b249faa686b3f7b57c/contract';
import endContract from '../../snapshots/2a58999b51b3503b8c6569732cb669bc995b8dc9956278b249faa686b3f7b57c/contract.json' with { type: 'json' };
import type { Contract as Start } from '../../snapshots/b8efd6dafa6fc9099e70e37bcab76c6104321edfc9b4844bebdb9e14ac5c518d/contract';
import startContract from '../../snapshots/b8efd6dafa6fc9099e70e37bcab76c6104321edfc9b4844bebdb9e14ac5c518d/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col, fn, primaryKey } from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'account_deletion',
        columns: [
          col('auth0_deleted_at', 'timestamptz', {
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('auth0_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('requested_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
        ],
        constraints: [primaryKey(['auth0_id'])],
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
