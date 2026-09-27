#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/6a7a31751ea63f3115c80d946f1e6b42f2d43fdd73c84894c9900648ce6bfd95/contract';
import startContract from '../../snapshots/6a7a31751ea63f3115c80d946f1e6b42f2d43fdd73c84894c9900648ce6bfd95/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/c9d11cbec8d8698eec9378f615f694ee856fcda93f97b0270c507997cef9ac8a/contract';
import endContract from '../../snapshots/c9d11cbec8d8698eec9378f615f694ee856fcda93f97b0270c507997cef9ac8a/contract.json' with { type: 'json' };
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
