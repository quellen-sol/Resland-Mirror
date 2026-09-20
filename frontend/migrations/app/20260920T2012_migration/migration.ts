#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/4cfa9de85dda60dd8eabf3b7d38fdfb73de17bf860102235b1e9c846e345aa23/contract';
import startContract from '../../snapshots/4cfa9de85dda60dd8eabf3b7d38fdfb73de17bf860102235b1e9c846e345aa23/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/4eb0f961df3960725ac7633a610724cdd543aba87feaf1871b7edfc95e8dedd8/contract';
import endContract from '../../snapshots/4eb0f961df3960725ac7633a610724cdd543aba87feaf1871b7edfc95e8dedd8/contract.json' with { type: 'json' };
import {
  Migration,
  MigrationCLI,
  checkExpression,
  col,
  fn,
  lit,
  primaryKey,
} from '@prisma/orm-postgres/migration';
import postgresStatic from '@prisma/orm-postgres/static';

const statics = postgresStatic<End>({ contractJson: endContract });
const { raw } = statics;

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'balance_purchase',
        columns: [
          col('amount_cents', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('cents', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('currency', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('status', 'text', {
            notNull: true,
            default: lit('PENDING'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'balance_purchase_status_check_37d7c798',
            "\"status\" IN ('PENDING', 'COMPLETED', 'EXPIRED')",
          ),
        ],
      }),
      this.createTable({
        schema: 'public',
        table: 'model_pricing',
        columns: [
          col('cents_per_1k_input', 'numeric', {
            notNull: true,
            codecRef: { codecId: 'pg/numeric@1' },
          }),
          col('cents_per_1k_output', 'numeric', {
            notNull: true,
            codecRef: { codecId: 'pg/numeric@1' },
          }),
          col('display_name', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('enabled', 'bool', {
            notNull: true,
            default: lit(true),
            codecRef: { codecId: 'pg/bool@1' },
          }),
          col('id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('sort_order', 'int4', {
            notNull: true,
            default: lit(0),
            codecRef: { codecId: 'pg/int4@1' },
          }),
        ],
        constraints: [primaryKey(['id'])],
      }),
      this.createTable({
        schema: 'public',
        table: 'token_usage',
        columns: [
          col('actual_cost_cents', 'numeric', { codecRef: { codecId: 'pg/numeric@1' } }),
          col('amount_cents', 'numeric', { notNull: true, codecRef: { codecId: 'pg/numeric@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('input_tokens', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('job_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('job_kind', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('model', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('openrouter_generation_ids', 'text[]', {
            notNull: true,
            default: lit([]),
            codecRef: { codecId: 'pg/text@1', many: true },
          }),
          col('output_tokens', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'token_usage_job_kind_check_74df029d',
            "\"job_kind\" IN ('SUGGESTION', 'TAILOR')",
          ),
          checkExpression(
            'token_usage_openrouter_generation_ids_elem_not_null_73635ad0',
            'array_position("openrouter_generation_ids", NULL) IS NULL',
          ),
        ],
      }),
      this.addColumn({
        schema: 'public',
        table: 'user',
        column: col('balance_cents', 'numeric', {
          notNull: true,
          default: lit('100'),
          codecRef: { codecId: 'pg/numeric@1' },
        }),
      }),
      this.addColumn({
        schema: 'public',
        table: 'user',
        column: col('site_admin', 'bool', {
          notNull: true,
          default: lit(false),
          codecRef: { codecId: 'pg/bool@1' },
        }),
      }),
      this.addColumn({
        schema: 'public',
        table: 'user',
        column: col('stripe_customer_id', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.addColumn({
        schema: 'public',
        table: 'user_suggestion',
        column: col('model', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.addColumn({
        schema: 'public',
        table: 'user_tailor_run',
        column: col('model', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.createIndex({
        schema: 'public',
        table: 'balance_purchase',
        index: 'balance_purchase_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'token_usage',
        index: 'token_usage_created_at_idx_225d8c0f',
        columns: ['created_at'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'token_usage',
        index: 'token_usage_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'balance_purchase',
        foreignKey: {
          name: 'balance_purchase_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'token_usage',
        foreignKey: {
          name: 'token_usage_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.dataTransform(statics.contract, 'seed-model_pricing-catalog', {
        check: () =>
          raw.sql`
            SELECT v.id FROM (VALUES
              ('openrouter:openai/gpt-5-mini'),
              ('openrouter:openai/gpt-5'),
              ('openrouter:anthropic/claude-sonnet-4.5'),
              ('openrouter:google/gemini-2.5-flash')
            ) AS v(id)
            WHERE NOT EXISTS (
              SELECT 1 FROM model_pricing mp WHERE mp.id = v.id
            )
          `.returnsRow({ id: 'pg/text@1' }),
        run: () =>
          raw.sql`
            INSERT INTO model_pricing
              (id, display_name, cents_per_1k_input, cents_per_1k_output, enabled, sort_order)
            VALUES
              ('openrouter:openai/gpt-5-mini', 'GPT-5 Mini', 0.03, 0.25, true, 1),
              ('openrouter:openai/gpt-5', 'GPT-5', 0.16, 1.25, true, 2),
              ('openrouter:anthropic/claude-sonnet-4.5', 'Claude Sonnet 4.5', 0.375, 1.9, true, 3),
              ('openrouter:google/gemini-2.5-flash', 'Gemini 2.5 Flash', 0.04, 0.315, true, 4)
            ON CONFLICT (id) DO NOTHING
          `.affectedCount(),
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
