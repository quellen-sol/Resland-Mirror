#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/376e701151882455ac9a9290b31faefbaf5d512847d139694f39f2a9a7745c4f/contract';
import startContract from '../../snapshots/376e701151882455ac9a9290b31faefbaf5d512847d139694f39f2a9a7745c4f/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/e57874e4160e37047d9c7a327d3afe64d5dc4a6cc03ab9d61d23cd63841e31da/contract';
import endContract from '../../snapshots/e57874e4160e37047d9c7a327d3afe64d5dc4a6cc03ab9d61d23cd63841e31da/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col } from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.addColumn({
        schema: 'public',
        table: 'user_base_experience',
        column: col('location', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
