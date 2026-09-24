#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/6c965d78add90876118915d52bfe06493f780185ac3956db6d5054bf657441d2/contract';
import endContract from '../../snapshots/6c965d78add90876118915d52bfe06493f780185ac3956db6d5054bf657441d2/contract.json' with { type: 'json' };
import type { Contract as Start } from '../../snapshots/be50cf86c51698349572a4290ed7a14af7374cfe98db45c480fd99b1d6e61037/contract';
import startContract from '../../snapshots/be50cf86c51698349572a4290ed7a14af7374cfe98db45c480fd99b1d6e61037/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col } from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.dropCheckConstraint({
        schema: 'public',
        table: 'balance_purchase',
        constraint: 'balance_purchase_status_check_37d7c798',
      }),
      this.addColumn({
        schema: 'public',
        table: 'balance_purchase',
        column: col('payment_intent_id', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.setDefault({
        schema: 'public',
        table: 'user',
        column: 'balance_cents',
        defaultSql: "DEFAULT '0'",
        operationClass: 'widening',
      }),
      this.addCheckConstraint({
        schema: 'public',
        table: 'balance_purchase',
        constraint: 'balance_purchase_status_check_e32ef9ef',
        expression: "\"status\" IN ('PENDING', 'COMPLETED', 'EXPIRED', 'REFUNDED')",
      }),
      this.addUnique({
        schema: 'public',
        table: 'token_usage',
        constraint: 'token_usage_job_kind_job_id_key',
        columns: ['job_kind', 'job_id'],
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
