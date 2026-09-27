#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/11d5ad4d18483b4a5be49b098be34ab924ce9c6f0724186f14efc8c15d1afc62/contract';
import startContract from '../../snapshots/11d5ad4d18483b4a5be49b098be34ab924ce9c6f0724186f14efc8c15d1afc62/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/787c1c218f39b6f79c7db522adeb4a8c58b137285b548d4c7b83b36d52982924/contract';
import endContract from '../../snapshots/787c1c218f39b6f79c7db522adeb4a8c58b137285b548d4c7b83b36d52982924/contract.json' with { type: 'json' };
import { Migration, MigrationCLI } from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.dropCheckConstraint({
        schema: 'public',
        table: 'user_suggestion',
        constraint: 'user_suggestion_status_check_8152fec2',
      }),
      this.addCheckConstraint({
        schema: 'public',
        table: 'user_suggestion',
        constraint: 'user_suggestion_status_check_fa868dec',
        expression: "\"status\" IN ('PROCESSING', 'WAITING_FOR_INPUT', 'COMPLETED', 'FAILED')",
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
