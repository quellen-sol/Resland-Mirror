#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/11d5ad4d18483b4a5be49b098be34ab924ce9c6f0724186f14efc8c15d1afc62/contract';
import endContract from '../../snapshots/11d5ad4d18483b4a5be49b098be34ab924ce9c6f0724186f14efc8c15d1afc62/contract.json' with { type: 'json' };
import type { Contract as Start } from '../../snapshots/31540dd849f6e9c286da91907829aea32ce114a05372af52009b69d742dd4a43/contract';
import startContract from '../../snapshots/31540dd849f6e9c286da91907829aea32ce114a05372af52009b69d742dd4a43/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col, lit } from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.addColumn({
        schema: 'public',
        table: 'user_base_skill',
        column: col('sort_order', 'int4', {
          notNull: true,
          default: lit(0),
          codecRef: { codecId: 'pg/int4@1' },
        }),
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
