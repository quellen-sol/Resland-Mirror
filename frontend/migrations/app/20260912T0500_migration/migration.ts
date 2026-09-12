#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/4e9db1e203bc658972e50583ab0c990925fd3ab2e6303a67270ae45f190b6e39/contract';
import endContract from '../../snapshots/4e9db1e203bc658972e50583ab0c990925fd3ab2e6303a67270ae45f190b6e39/contract.json' with { type: 'json' };
import { Migration, MigrationCLI } from '@prisma/orm-postgres/migration';

export default class M extends Migration<never, End> {
  override readonly endContractJson = endContract;

  override get operations() {
    return [];
  }
}

MigrationCLI.run(import.meta.url, M);
