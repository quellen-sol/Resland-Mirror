#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/2d9e997e862ea3eb741cd87eb5ed1798cf439c142125663097f849b14b26463b/contract';
import endContract from '../../snapshots/2d9e997e862ea3eb741cd87eb5ed1798cf439c142125663097f849b14b26463b/contract.json' with { type: 'json' };
import type { Contract as Start } from '../../snapshots/31540dd849f6e9c286da91907829aea32ce114a05372af52009b69d742dd4a43/contract';
import startContract from '../../snapshots/31540dd849f6e9c286da91907829aea32ce114a05372af52009b69d742dd4a43/contract.json' with { type: 'json' };
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
