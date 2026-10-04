#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/b8efd6dafa6fc9099e70e37bcab76c6104321edfc9b4844bebdb9e14ac5c518d/contract';
import endContract from '../../snapshots/b8efd6dafa6fc9099e70e37bcab76c6104321edfc9b4844bebdb9e14ac5c518d/contract.json' with { type: 'json' };
import type { Contract as Start } from '../../snapshots/fbcfb6d73d6292fc83fe93d684ca06b76cc186f9582c456695cad477992ccb40/contract';
import startContract from '../../snapshots/fbcfb6d73d6292fc83fe93d684ca06b76cc186f9582c456695cad477992ccb40/contract.json' with { type: 'json' };
import {
  Migration,
  MigrationCLI,
  checkExpression,
  col,
  fn,
  primaryKey,
} from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'page_view',
        columns: [
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('path', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('prev_path', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('source', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('source_name', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('utm_campaign', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('visit_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'page_view_source_check_c4100b70',
            "\"source\" IN ('SEARCH', 'AI', 'SOCIAL', 'REFERRAL', 'DIRECT', 'INTERNAL')",
          ),
        ],
      }),
      this.createIndex({
        schema: 'public',
        table: 'page_view',
        index: 'page_view_created_at_idx_225d8c0f',
        columns: ['created_at'],
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
